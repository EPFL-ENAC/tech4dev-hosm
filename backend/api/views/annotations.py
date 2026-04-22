"""
Manage annotations and users
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

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
)
from api.services.auth import get_current_user

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

    if data.polygon is not None:
        annotation.polygon = data.polygon
    if data.damage_level is not None:
        annotation.damage_level = data.damage_level

    session.add(annotation)
    await session.commit()
    await session.refresh(annotation)

    return annotation


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
