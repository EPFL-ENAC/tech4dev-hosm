"""
Manage annotations and users
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlmodel import select

from api.db import get_session
from api.models.annotations import (
    AnnotatedImage,
    AnnotatedImageCreate,
    AnnotatedImageRead,
    AnnotatedImagesCountsResponse,
    AnnotatedImageUpdate,
    Annotation,
    AnnotationCreate,
    AnnotationRead,
    AnnotationUpdate,
    CompletionStatus,
    User,
    UserListResponse,
    ValidationStatus,
)
from api.services.annotations import (
    get_users as get_users_service,
)
from api.services.auth import get_current_reviewer, get_current_user

VALID_USER_SORT_FIELDS = {
    "full_name",
    "email",
    "role",
    "created_at",
    "last_action_at",
    "annotated_images_count",
    "non_reviewed_images_count",
    "total_annotations_count",
}


logger = logging.getLogger("uvicorn.error")
router = APIRouter()


@router.post("/annotated-images/")
async def create_annotated_image(
    data: AnnotatedImageCreate,
    session=Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AnnotatedImage:
    assert current_user.id is not None
    image = AnnotatedImage(image_path=data.image_path, annotator_id=current_user.id)

    current_user.last_action_at = datetime.now()
    session.add(image)
    session.add(current_user)
    try:
        await session.commit()
        await session.refresh(image)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Image already exists in dataset")

    return image


@router.get("/annotated-images/")
async def get_annotated_images(
    annotator_id: int | None = Query(default=None, ge=1),
    session=Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[AnnotatedImageRead]:
    """Get annotated images for the current user, or for a specific annotator if the user is a reviewer."""
    if annotator_id is not None:
        if not current_user.is_reviewer:
            raise HTTPException(status_code=403, detail="Access denied: reviewers only")
        target_annotator_id = annotator_id
    else:
        assert current_user.id is not None
        target_annotator_id = current_user.id

    images = await session.exec(
        select(AnnotatedImage).where(AnnotatedImage.annotator_id == target_annotator_id)
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

    if data.completion_status is not None:
        image.completion_status = data.completion_status

    current_user.last_action_at = datetime.now()
    session.add(image)
    session.add(current_user)
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

    current_user.last_action_at = datetime.now()
    session.add(current_user)
    await session.delete(image)
    await session.commit()


@router.get("/annotated-images-counts")
async def get_annotated_images_counts(
    session=Depends(get_session),
    current_user: User = Depends(get_current_reviewer),
) -> AnnotatedImagesCountsResponse:
    """Get the counts of annotated images (per image_path)."""
    total = await session.scalar(select(func.count(AnnotatedImage.id)))
    unique = await session.scalar(
        select(func.count(func.distinct(AnnotatedImage.image_path)))
    )
    completed = await session.scalar(
        select(func.count(AnnotatedImage.id)).where(
            AnnotatedImage.completion_status == CompletionStatus.COMPLETED
        )
    )
    irrelevant = await session.scalar(
        select(func.count(AnnotatedImage.id)).where(
            AnnotatedImage.completion_status == CompletionStatus.IRRELEVANT
        )
    )
    approved = await session.scalar(
        select(func.count(AnnotatedImage.id)).where(
            AnnotatedImage.validation_status == ValidationStatus.APPROVED
        )
    )
    rejected = await session.scalar(
        select(func.count(AnnotatedImage.id)).where(
            AnnotatedImage.validation_status == ValidationStatus.REJECTED
        )
    )
    annotators = await session.scalar(
        select(func.count(func.distinct(AnnotatedImage.annotator_id)))
    )

    return AnnotatedImagesCountsResponse(
        total=total or 0,
        unique=unique or 0,
        completed=completed or 0,
        irrelevant=irrelevant or 0,
        approved=approved or 0,
        rejected=rejected or 0,
        annotators=annotators or 0,
    )


@router.post("/")
async def create_annotation(
    data: AnnotationCreate,
    session=Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AnnotationRead:
    image = await session.get(AnnotatedImage, data.annotated_image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Allow if user owns the image or is a reviewer
    if image.annotator_id != current_user.id and not current_user.is_reviewer:
        raise HTTPException(
            status_code=403, detail="Not authorized to annotate this image"
        )

    annotation = Annotation(
        annotated_image_id=data.annotated_image_id,
        polygon=data.polygon,
        damage_level=data.damage_level,
    )

    current_user.last_action_at = datetime.now()
    session.add(annotation)
    session.add(current_user)
    await session.commit()
    await session.refresh(annotation)

    return AnnotationRead.model_validate(annotation)


@router.get("/download", description="Download all annotation data in JSON format.")
async def download_annotations(
    session=Depends(get_session),
    current_user: User = Depends(get_current_reviewer),
) -> Response:
    """Fetch all annotated images with their annotations and return grouped by image_path.

    Replaces annotator/reviewer references with their emails.
    Only keeps polygon and damage_level per annotation.
    """
    images = (
        await session.exec(
            select(AnnotatedImage).options(
                joinedload(AnnotatedImage.annotator),
                joinedload(AnnotatedImage.reviewer),
            )
        )
    ).all()

    result = {}
    for image in images:
        image_path = image.image_path
        annotator_email = image.annotator.email if image.annotator else None
        reviewer_email = image.reviewer.email if image.reviewer else None

        annotations = [
            {
                "polygon": ann.polygon,
                "damage_level": ann.damage_level,
            }
            for ann in image.annotations
        ]

        entry = {
            "annotator": annotator_email,
            "reviewer": reviewer_email,
            "completion_status": image.completion_status,
            "validation_status": image.validation_status,
            "annotations": annotations,
        }

        if image_path not in result:
            result[image_path] = []
        result[image_path].append(entry)

    return JSONResponse(content=result)


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
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Allow if user owns the image or is a reviewer
    if image.annotator_id != current_user.id and not current_user.is_reviewer:
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
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Allow if user owns the image or is a reviewer
    if image.annotator_id != current_user.id and not current_user.is_reviewer:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this annotation"
        )

    if data.polygon is not None:
        annotation.polygon = data.polygon
    if data.damage_level is not None:
        annotation.damage_level = data.damage_level

    current_user.last_action_at = datetime.now()
    session.add(annotation)
    session.add(current_user)
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
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Allow if user owns the image or is a reviewer
    if image.annotator_id != current_user.id and not current_user.is_reviewer:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this annotation"
        )

    current_user.last_action_at = datetime.now()
    session.add(current_user)
    await session.delete(annotation)
    await session.commit()


@router.post("/annotated-images/{annotated_image_id}/approve")
async def approve_annotated_image(
    annotated_image_id: int,
    session=Depends(get_session),
    current_user: User = Depends(get_current_reviewer),
) -> AnnotatedImageRead:
    """Approve an annotated image."""
    image = await session.get(AnnotatedImage, annotated_image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Annotated image not found")

    image.validation_status = ValidationStatus.APPROVED
    image.reviewer_id = current_user.id
    image.reviewed_at = datetime.now()

    current_user.last_action_at = datetime.now()
    session.add(image)
    session.add(current_user)
    await session.commit()
    await session.refresh(image)

    return image


@router.post("/annotated-images/{annotated_image_id}/reject")
async def reject_annotated_image(
    annotated_image_id: int,
    session=Depends(get_session),
    current_user: User = Depends(get_current_reviewer),
) -> AnnotatedImageRead:
    """Reject an annotated image."""
    image = await session.get(AnnotatedImage, annotated_image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Annotated image not found")

    image.validation_status = ValidationStatus.REJECTED
    image.reviewer_id = current_user.id
    image.reviewed_at = datetime.now()

    current_user.last_action_at = datetime.now()
    session.add(image)
    session.add(current_user)
    await session.commit()
    await session.refresh(image)

    return image


@router.get("/users/", description="Get paginated users with annotation statistics.")
async def get_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="full_name"),
    sort_order: str = Query(default="asc"),
    session=Depends(get_session),
    current_user: User = Depends(get_current_reviewer),
) -> UserListResponse:
    if sort_by not in VALID_USER_SORT_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by field. Must be one of: {', '.join(sorted(VALID_USER_SORT_FIELDS))}",
        )
    if sort_order not in ("asc", "desc"):
        raise HTTPException(
            status_code=400,
            detail="sort_order must be 'asc' or 'desc'",
        )

    result = await get_users_service(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        session=session,
    )

    return UserListResponse(**result)
