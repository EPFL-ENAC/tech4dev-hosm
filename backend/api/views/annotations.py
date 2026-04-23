"""
Manage annotations and users
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, desc
from sqlalchemy.exc import IntegrityError
from sqlmodel import func, select

from api.db import get_session
from api.models.annotations import (
    AnnotatedImage,
    AnnotatedImageCreate,
    AnnotatedImageRead,
    AnnotatedImageUpdate,
    Annotation,
    AnnotationCreate,
    AnnotationRead,
    AnnotationUpdate,
    User,
    UserListResponse,
    UserReadWithStats,
)
from api.services.auth import get_current_reviewer, get_current_user

logger = logging.getLogger("uvicorn.error")
router = APIRouter()


@router.post("/annotated-images/")
async def create_annotated_image(
    data: AnnotatedImageCreate,
    session=Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AnnotatedImage:
    image = AnnotatedImage(image_path=data.image_path, annotator_id=current_user.id)

    session.add(image)
    try:
        await session.commit()
        await session.refresh(image)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Image already exists in dataset")

    return image


@router.get("/annotated-images/")
async def get_annotated_images(
    session=Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[AnnotatedImageRead]:
    images = await session.exec(
        select(AnnotatedImage).where(AnnotatedImage.annotator_id == current_user.id)
    )
    return list(images)


@router.get("/annotated-images/{annotated_image_id}")
async def get_annotated_image(
    annotated_image_id: int,
    session=Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AnnotatedImageRead:
    image = await session.get(AnnotatedImage, annotated_image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Annotated image not found")

    if image.annotator_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this image"
        )

    return image


@router.put("/annotated-images/{annotated_image_id}")
async def update_annotated_image(
    annotated_image_id: int,
    data: AnnotatedImageUpdate,
    session=Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AnnotatedImageRead:
    image = await session.get(AnnotatedImage, annotated_image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Annotated image not found")

    if image.annotator_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this image"
        )

    if data.completed is not None:
        image.completed = data.completed

    session.add(image)
    await session.commit()
    await session.refresh(image)

    return image


@router.delete("/annotated-images/{annotated_image_id}", status_code=204)
async def delete_annotated_image(
    annotated_image_id: int,
    session=Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    image = await session.get(AnnotatedImage, annotated_image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Annotated image not found")

    if image.annotator_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this image"
        )

    await session.delete(image)
    await session.commit()


@router.post("/")
async def create_annotation(
    data: AnnotationCreate,
    session=Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AnnotationRead:
    image = await session.get(AnnotatedImage, data.annotated_image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    if image.annotator_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to annotate this image"
        )

    annotation = Annotation(
        annotated_image_id=data.annotated_image_id,
        polygon=data.polygon,
        damage_level=data.damage_level,
    )

    session.add(annotation)
    await session.commit()
    await session.refresh(annotation)

    return AnnotationRead.model_validate(annotation)


@router.get("/{annotation_id}")
async def get_annotation(
    annotation_id: int,
    session=Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AnnotationRead:
    annotation = await session.get(Annotation, annotation_id)
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")

    image = await session.get(AnnotatedImage, annotation.annotated_image_id)
    if not image or image.annotator_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this annotation"
        )

    return annotation


@router.put("/{annotation_id}")
async def update_annotation(
    annotation_id: int,
    data: AnnotationUpdate,
    session=Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AnnotationRead:
    annotation = await session.get(Annotation, annotation_id)
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")

    image = await session.get(AnnotatedImage, annotation.annotated_image_id)
    if not image or image.annotator_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this annotation"
        )

    if data.polygon is not None:
        annotation.polygon = data.polygon
    if data.damage_level is not None:
        annotation.damage_level = data.damage_level

    session.add(annotation)
    await session.commit()
    await session.refresh(annotation)

    return annotation


@router.delete("/{annotation_id}", status_code=204)
async def delete_annotation(
    annotation_id: int,
    session=Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    annotation = await session.get(Annotation, annotation_id)
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")

    image = await session.get(AnnotatedImage, annotation.annotated_image_id)
    if not image or image.annotator_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this annotation"
        )

    await session.delete(annotation)
    await session.commit()


def _sort_order_func(order: str):
    return desc if order == "desc" else asc


@router.get("/users/")
async def get_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="full_name"),
    sort_order: str = Query(default="asc"),
    session=Depends(get_session),
    current_user: User = Depends(get_current_reviewer),
) -> UserListResponse:
    valid_sort_fields = [
        "full_name",
        "email",
        "created_at",
        "annotated_images_count",
        "total_annotations_count",
    ]
    if sort_by not in valid_sort_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}",
        )

    if sort_order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sort_order must be 'asc' or 'desc'",
        )

    offset = (page - 1) * page_size

    total_users_result = await session.exec(select(func.count()).select_from(User))
    total_users = total_users_result.one()

    sort_by_counts = sort_by in ["annotated_images_count", "total_annotations_count"]

    if sort_by_counts:
        all_users_result = await session.exec(select(User))
        all_users = all_users_result.all()
        all_user_ids = [user.id for user in all_users if user.id is not None]

        images_count_statement = (
            select(AnnotatedImage.annotator_id, func.count(AnnotatedImage.id))  # type: ignore[arg-type]
            .where(AnnotatedImage.annotator_id.in_(all_user_ids))  # type: ignore[attr-defined]
            .group_by(AnnotatedImage.annotator_id)  # type: ignore[arg-type]
        )
        images_counts_result = await session.exec(images_count_statement)
        images_counts = {row[0]: row[1] for row in images_counts_result}

        annotations_count_statement = (
            select(Annotation.annotated_image_id, func.count(Annotation.id))  # type: ignore[arg-type]
            .join(AnnotatedImage, Annotation.annotated_image_id == AnnotatedImage.id)  # type: ignore[arg-type]
            .where(AnnotatedImage.annotator_id.in_(all_user_ids))  # type: ignore[attr-defined]
            .group_by(Annotation.annotated_image_id)  # type: ignore[arg-type]
        )
        annotations_counts_per_image = await session.exec(annotations_count_statement)
        annotations_per_image = dict(annotations_counts_per_image.all())

        user_annotations_counts = {}
        for annotator_id in all_user_ids:
            total = 0
            images_query = select(AnnotatedImage.id).where(
                AnnotatedImage.annotator_id == annotator_id
            )
            image_ids_result = await session.exec(images_query)
            image_ids = image_ids_result.all()
            for image_id in image_ids:
                total += annotations_per_image.get(image_id, 0)
            user_annotations_counts[annotator_id] = total

        users_with_stats = []
        for user in all_users:
            images_count = images_counts.get(user.id, 0)
            annotations_count = user_annotations_counts.get(user.id, 0)
            users_with_stats.append((user, images_count, annotations_count))

        if sort_by == "annotated_images_count":
            users_with_stats.sort(key=lambda x: x[1], reverse=(sort_order == "desc"))
        else:
            users_with_stats.sort(key=lambda x: x[2], reverse=(sort_order == "desc"))

        users_with_stats = users_with_stats[offset : offset + page_size]
        user_items = [
            UserReadWithStats(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                is_reviewer=user.is_reviewer,
                created_at=user.created_at,
                annotated_images_count=images_count,
                total_annotations_count=annotations_count,
            )
            for user, images_count, annotations_count in users_with_stats
        ]
    else:
        user_sort_field = getattr(User, sort_by)
        statement = (
            select(User)
            .order_by(_sort_order_func(sort_order)(user_sort_field))
            .offset(offset)
            .limit(page_size)
        )

        results = await session.exec(statement)
        users = results.all()

        user_ids = [user.id for user in users if user.id is not None]

        images_count_statement = (
            select(AnnotatedImage.annotator_id, func.count(AnnotatedImage.id))
            .where(AnnotatedImage.annotator_id.in_(user_ids))
            .group_by(AnnotatedImage.annotator_id)
        )
        images_counts_result = await session.exec(images_count_statement)
        images_counts = {row[0]: row[1] for row in images_counts_result}

        annotations_count_statement = (
            select(Annotation.annotated_image_id, func.count(Annotation.id))
            .join(AnnotatedImage, Annotation.annotated_image_id == AnnotatedImage.id)
            .where(AnnotatedImage.annotator_id.in_(user_ids))
            .group_by(Annotation.annotated_image_id)
        )
        annotations_counts_per_image = await session.exec(annotations_count_statement)
        annotations_per_image = dict(annotations_counts_per_image.all())

        user_annotations_counts = {}
        for annotator_id in user_ids:
            total = 0
            images_query = select(AnnotatedImage.id).where(
                AnnotatedImage.annotator_id == annotator_id
            )
            image_ids_result = await session.exec(images_query)
            image_ids = image_ids_result.all()
            for image_id in image_ids:
                total += annotations_per_image.get(image_id, 0)
            user_annotations_counts[annotator_id] = total

        user_items = []
        for user in users:
            images_count = images_counts.get(user.id, 0)
            annotations_count = user_annotations_counts.get(user.id, 0)

            user_items.append(
                UserReadWithStats(
                    id=user.id,
                    email=user.email,
                    full_name=user.full_name,
                    is_reviewer=user.is_reviewer,
                    created_at=user.created_at,
                    annotated_images_count=images_count,
                    total_annotations_count=annotations_count,
                )
            )

    total_pages = (total_users + page_size - 1) // page_size if total_users > 0 else 1

    return UserListResponse(
        items=user_items,
        total=total_users,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
