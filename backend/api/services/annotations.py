import random
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import asc, delete, desc, func, select

# SQLModel's select returns a SelectOfScalar, so session.exec() yields entities;
# a plain SQLAlchemy select would yield Row tuples instead.
from sqlmodel import select as sm_select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models.annotations import (
    AnnotatedImage,
    Annotation,
    DamageLevel,
    User,
    UserReadWithStats,
)


def _build_users_queries(sort_by: str, sort_order: str):
    """Build the main user query (with annotation statistics) and a count query.

    Returns a tuple ``(main_query, count_query)``.
    """
    sort_direction = desc if sort_order == "desc" else asc

    image_counts_cte = (
        select(
            AnnotatedImage.annotator_id,
            func.count(AnnotatedImage.id).label("annotated_images_count"),
        )
        .group_by(AnnotatedImage.annotator_id)
        .cte("image_counts")
    )

    non_reviewed_images_cte = (
        select(
            AnnotatedImage.annotator_id,
            func.count(AnnotatedImage.id).label("non_reviewed_images_count"),
        )
        .where(AnnotatedImage.reviewer_id.is_(None))
        .group_by(AnnotatedImage.annotator_id)
        .cte("non_reviewed_images")
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
        func.coalesce(non_reviewed_images_cte.c.non_reviewed_images_count, 0).label(
            "non_reviewed_images_count"
        ),
        func.coalesce(annotation_counts_cte.c.total_annotations_count, 0).label(
            "total_annotations_count"
        ),
    ).select_from(
        User.__table__.join(
            image_counts_cte, User.id == image_counts_cte.c.annotator_id, isouter=True
        )
        .join(
            non_reviewed_images_cte,
            User.id == non_reviewed_images_cte.c.annotator_id,
            isouter=True,
        )
        .join(
            annotation_counts_cte,
            User.id == annotation_counts_cte.c.annotator_id,
            isouter=True,
        )
    )

    if sort_by == "annotated_images_count":
        main_query = main_query.order_by(
            sort_direction(func.coalesce(image_counts_cte.c.annotated_images_count, 0))
        )
    elif sort_by == "non_reviewed_images_count":
        main_query = main_query.order_by(
            sort_direction(
                func.coalesce(non_reviewed_images_cte.c.non_reviewed_images_count, 0)
            )
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
            non_reviewed_images_cte, User.id == non_reviewed_images_cte.c.annotator_id
        )
        .outerjoin(
            annotation_counts_cte, User.id == annotation_counts_cte.c.annotator_id
        )
    )
    return main_query, count_query


async def _build_user_items(
    user_rows: list, session: AsyncSession
) -> list[UserReadWithStats]:
    """Build UserReadWithStats items (including annotating time) from raw rows."""
    annotator_ids = [row.id for row in user_rows if row.id is not None]
    annotating_seconds = await get_annotating_seconds_by_annotator(
        annotator_ids, session
    )

    return [
        UserReadWithStats(
            id=row.id,
            email=row.email,
            full_name=row.full_name,
            is_reviewer=row.is_reviewer,
            created_at=row.created_at,
            last_action_at=row.last_action_at,
            annotated_images_count=row.annotated_images_count,
            non_reviewed_images_count=row.non_reviewed_images_count,
            total_annotations_count=row.total_annotations_count,
            annotation_time_seconds=annotating_seconds.get(row.id, 0),
        )
        for row in user_rows
    ]


async def get_users(
    page: int,
    page_size: int,
    sort_by: str,
    sort_order: str,
    session: AsyncSession,
) -> dict:
    offset = (page - 1) * page_size
    main_query, count_query = _build_users_queries(sort_by, sort_order)
    total_users = await session.scalar(count_query)

    main_query = main_query.offset(offset).limit(page_size)
    results = await session.exec(main_query)
    user_rows = results.all()

    user_items = await _build_user_items(user_rows, session)

    total_pages = (total_users + page_size - 1) // page_size if total_users > 0 else 1

    return {
        "items": user_items,
        "total": total_users,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


async def get_all_users(session: AsyncSession) -> list[UserReadWithStats]:
    """Fetch all users with their annotation statistics (no pagination)."""
    main_query, _ = _build_users_queries(sort_by="id", sort_order="asc")
    results = await session.exec(main_query)
    user_rows = results.all()

    return await _build_user_items(user_rows, session)


def compute_annotating_time(image: AnnotatedImage) -> timedelta:
    """Compute the total time spent annotating one image.

    Collect the effective timestamp of each annotation (updated_at when set,
    otherwise created_at), batch them by day, and for each day take the span
    between the latest and the earliest timestamp. A day with a single
    annotation contributes zero. Return the sum over all days.
    """
    timestamps_by_day: dict[date, list[datetime]] = defaultdict(list)

    for annotation in image.annotations:
        if annotation.updated_at is not None:
            timestamp = annotation.updated_at
        else:
            timestamp = annotation.created_at
        if timestamp is None:
            continue
        # SQLite returns naive UTC datetimes; Postgres returns aware ones.
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        timestamps_by_day[timestamp.date()].append(timestamp)

    total = timedelta()
    for timestamps in timestamps_by_day.values():
        if len(timestamps) < 2:
            continue  # Single annotation on this day: zero time.
        total += max(timestamps) - min(timestamps)
    return total


async def get_annotating_seconds_by_annotator(
    annotator_ids: list[int], session: AsyncSession
) -> dict[int, int]:
    """Compute the total annotating time (seconds) for each given annotator.

    Loads all images (with annotations) of the given annotators into memory;
    move the computation into SQL if the dataset grows a lot.
    """
    if not annotator_ids:
        return {}

    images = await session.exec(
        sm_select(AnnotatedImage).where(AnnotatedImage.annotator_id.in_(annotator_ids))
    )
    totals: dict[int, timedelta] = defaultdict(timedelta)
    for image in images:
        if image.annotator_id is not None:
            totals[image.annotator_id] += compute_annotating_time(image)

    return {
        annotator_id: round(total.total_seconds())
        for annotator_id, total in totals.items()
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
                annotated_image_id=image.id,  # type: ignore
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
