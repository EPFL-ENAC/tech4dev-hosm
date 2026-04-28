from sqlalchemy import asc, desc, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models.annotations import (
    AnnotatedImage,
    Annotation,
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
    """Get paginated users with annotation statistics.

    Uses CTEs to calculate counts at the database level for efficiency.
    Supports sorting by user fields and computed counts.

    Note: Input validation is performed at the router layer before calling this service.
    """
    offset = (page - 1) * page_size
    sort_direction = desc if sort_order == "desc" else asc

    # Build CTEs for counts
    image_counts_cte = (
        select(
            AnnotatedImage.annotator_id,
            func.count(AnnotatedImage.id).label("annotated_images_count"),
        )
        .group_by(AnnotatedImage.annotator_id)
        .cte("image_counts")
    )

    annotation_counts_cte = (
        select(
            AnnotatedImage.annotator_id,
            func.count(Annotation.id).label("total_annotations_count"),
        )
        .join(AnnotatedImage, Annotation.annotated_image_id == AnnotatedImage.id)  # type: ignore[attr-defined]
        .group_by(AnnotatedImage.annotator_id)  # type: ignore[attr-defined]
        .cte("annotation_counts")
    )

    # Build main query with CTEs and LEFT JOINs
    # Access CTE columns via .c. attribute for type safety
    main_query = (
        select(
            User.id,
            User.email,
            User.full_name,
            User.is_reviewer,
            User.created_at,
            func.coalesce(image_counts_cte.c.annotated_images_count, 0).label(
                "annotated_images_count"
            ),
            func.coalesce(annotation_counts_cte.c.total_annotations_count, 0).label(
                "total_annotations_count"
            ),
        )
        .select_from(User)
        .outerjoin(image_counts_cte, User.id == image_counts_cte.c.annotator_id)
        .outerjoin(
            annotation_counts_cte, User.id == annotation_counts_cte.c.annotator_id
        )
    )

    # Add ORDER BY based on sort field
    if sort_by == "annotated_images_count":
        # Sort by CTE column
        main_query = main_query.order_by(  # type: ignore[attr-defined]
            sort_direction(image_counts_cte.c.annotated_images_count)
        )
    elif sort_by == "total_annotations_count":
        # Sort by CTE column
        main_query = main_query.order_by(  # type: ignore[attr-defined]
            sort_direction(annotation_counts_cte.c.total_annotations_count)
        )
    else:
        # Sort by User model column
        user_sort_field = getattr(User, sort_by)
        main_query = main_query.order_by(sort_direction(user_sort_field))  # type: ignore[attr-defined]

    # Get total count for pagination metadata (before pagination is applied)
    # Use the same base query without ORDER BY, OFFSET, LIMIT for accurate count
    count_query = (
        select(func.count())
        .select_from(User)
        .outerjoin(image_counts_cte, User.id == image_counts_cte.c.annotator_id)
        .outerjoin(
            annotation_counts_cte, User.id == annotation_counts_cte.c.annotator_id
        )
    )
    total_users = await session.scalar(count_query)

    # Add pagination to main query
    main_query = main_query.offset(offset).limit(page_size)

    # Execute main query
    results = await session.exec(main_query)
    user_rows = results.all()

    # Build response objects
    user_items = [
        UserReadWithStats(
            id=row.id,
            email=row.email,
            full_name=row.full_name,
            is_reviewer=row.is_reviewer,
            created_at=row.created_at,
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
