import random

from sqlalchemy import asc, delete, desc, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models.annotations import (
    AnnotatedImage,
    Annotation,
    DamageLevel,
    User,
    UserReadWithStats,
)


async def get_users(
    page: int,
    page_size: int,
    sort_by: str,
    sort_order: str,
    session: AsyncSession,
) -> dict:
    offset = (page - 1) * page_size
    sort_direction = desc if sort_order == "desc" else asc

    image_counts_cte = (
        select(
            AnnotatedImage.annotator_id,
            func.count(AnnotatedImage.id).label("annotated_images_count"),
        )
        .group_by(AnnotatedImage.annotator_id)
        .cte("image_counts")
    )

    annotation_counts_per_image_cte = (
        select(
            Annotation.annotated_image_id,
            func.count(Annotation.id).label("total_annotations_count"),
        )
        .group_by(Annotation.annotated_image_id)
        .cte("annotation_counts_per_image")
    )

    annotation_counts_cte = (
        select(
            AnnotatedImage.annotator_id,
            func.sum(annotation_counts_per_image_cte.c.total_annotations_count).label(
                "total_annotations_count"
            ),
        )
        .select_from(
            AnnotatedImage.__table__.join(
                annotation_counts_per_image_cte,
                AnnotatedImage.id
                == annotation_counts_per_image_cte.c.annotated_image_id,
            )
        )
        .group_by(AnnotatedImage.annotator_id)
        .cte("annotation_counts")
    )

    main_query = select(
        User.id,
        User.email,
        User.full_name,
        User.is_reviewer,
        User.created_at,
        User.last_action_at,
        func.coalesce(image_counts_cte.c.annotated_images_count, 0).label(
            "annotated_images_count"
        ),
        func.coalesce(annotation_counts_cte.c.total_annotations_count, 0).label(
            "total_annotations_count"
        ),
    ).select_from(
        User.__table__.join(
            image_counts_cte, User.id == image_counts_cte.c.annotator_id, isouter=True
        ).join(
            annotation_counts_cte,
            User.id == annotation_counts_cte.c.annotator_id,
            isouter=True,
        )
    )

    if sort_by == "annotated_images_count":
        main_query = main_query.order_by(
            sort_direction(func.coalesce(image_counts_cte.c.annotated_images_count, 0))
        )
    elif sort_by == "total_annotations_count":
        main_query = main_query.order_by(
            sort_direction(
                func.coalesce(annotation_counts_cte.c.total_annotations_count, 0)
            )
        )
    elif sort_by == "role":
        main_query = main_query.order_by(
            sort_direction(func.coalesce(User.is_reviewer, False))
        )
    else:
        user_sort_field = getattr(User, sort_by)
        main_query = main_query.order_by(sort_direction(user_sort_field))

    count_query = (
        select(func.count())
        .select_from(User)
        .outerjoin(image_counts_cte, User.id == image_counts_cte.c.annotator_id)
        .outerjoin(
            annotation_counts_cte, User.id == annotation_counts_cte.c.annotator_id
        )
    )
    total_users = await session.scalar(count_query)

    main_query = main_query.offset(offset).limit(page_size)
    results = await session.exec(main_query)
    user_rows = results.all()

    user_items = [
        UserReadWithStats(
            id=row.id,
            email=row.email,
            full_name=row.full_name,
            is_reviewer=row.is_reviewer,
            created_at=row.created_at,
            last_action_at=row.last_action_at,
            annotated_images_count=row.annotated_images_count,
            total_annotations_count=row.total_annotations_count,
        )
        for row in user_rows
    ]

    total_pages = (total_users + page_size - 1) // page_size if total_users > 0 else 1

    return {
        "items": user_items,
        "total": total_users,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


async def create_mock_data(session: AsyncSession) -> dict:
    """Create mock data: 1 reviewer, 2 annotators, 2-4 annotated images each, 1-5 annotations per image.

    Drops existing mock data first if any users exist.
    """
    # Check if data already exists and delete if present
    result = await session.exec(select(User))
    existing_users = result.all()
    if existing_users:
        # Delete in reverse dependency order
        await session.exec(delete(Annotation))
        await session.exec(delete(AnnotatedImage))
        await session.exec(delete(User))

        await session.commit()

    # Create 1 reviewer
    reviewer = User(
        email="reviewer@example.com",
        full_name="Test Reviewer",
        is_reviewer=True,
    )
    session.add(reviewer)
    await session.flush()
    reviewer_email = reviewer.email

    # Create 100 annotators
    annotators = []
    annotator_emails = []
    for i in range(100):
        annotator = User(
            email=f"annotator{i + 1}@example.com",
            full_name=f"Test Annotator {i + 1}",
            is_reviewer=False,
        )
        session.add(annotator)
        annotators.append(annotator)
        annotator_emails.append(annotator.email)
    await session.flush()

    # Create 2-4 annotated images per annotator
    image_paths = [
        "images/image_001.jpg",
        "images/image_002.jpg",
        "images/image_003.jpg",
        "images/image_004.jpg",
        "images/image_005.jpg",
    ]

    created_images: list[AnnotatedImage] = []
    for annotator in annotators:
        num_images = random.randint(2, 4)
        for j in range(num_images):
            image_path = (
                image_paths[len(created_images)]
                if len(created_images) < len(image_paths)
                else f"images/image_{len(created_images) + 1:03d}.jpg"
            )
            annotated_image = AnnotatedImage(
                image_path=image_path,
                annotator_id=annotator.id,
            )
            session.add(annotated_image)
            created_images.append(annotated_image)
    await session.flush()

    # Create 1-5 annotations per image
    damage_levels = [DamageLevel.UNSET, DamageLevel.UNDAMAGED, DamageLevel.DAMAGED]
    total_annotations = 0
    for image in created_images:
        num_annotations = random.randint(1, 5)
        total_annotations += num_annotations
        for _ in range(num_annotations):
            # Generate random polygon points (at least 3 points for a valid polygon)
            num_points = random.randint(3, 6)
            polygon = [
                [round(random.uniform(0, 100), 2), round(random.uniform(0, 100), 2)]
                for _ in range(num_points)
            ]
            annotation = Annotation(
                polygon=polygon,
                damage_level=random.choice(damage_levels),
                annotated_image_id=image.id,
            )
            session.add(annotation)

    await session.commit()

    return {
        "message": "Mock data created successfully",
        "reviewer": reviewer_email,
        "annotators": annotator_emails,
        "images": len(created_images),
        "annotations": total_annotations,
    }
