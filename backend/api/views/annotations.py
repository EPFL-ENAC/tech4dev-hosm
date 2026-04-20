"""
Manage annotations and users
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from api.config import config
from api.db import get_session
from api.models.annotations import (
    AnnotatedImage,
    AnnotatedImageCreate,
    Annotation,
    AnnotationCreate,
    AnnotationUpdate,
    User,
    UserCreate,
)

logger = logging.getLogger("uvicorn.error")
router = APIRouter()


@router.post("/users", response_model=User)
async def create_user(data: UserCreate, session=Depends(get_session)) -> User:
    user = User(
        email=data.email,
        first_name=data.first_name,
        last_name=data.last_name,
        is_reviewer=data.is_reviewer,
    )

    existing_user = (
        await session.exec(select(User).where(User.email == user.email))
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


@router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int, session=Depends(get_session)) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.post("/annotated-images/", response_model=AnnotatedImage)
async def create_annotated_image(
    data: AnnotatedImageCreate, session=Depends(get_session)
) -> AnnotatedImage:
    annotator = await session.get(User, data.annotator_id)
    if not annotator:
        raise HTTPException(status_code=404, detail="Annotator not found")

    image = AnnotatedImage(image_url=data.image_url, annotator_id=data.annotator_id)

    session.add(image)
    await session.commit()
    await session.refresh(image)

    return image


@router.get("/annotated-images/{annotated_image_id}", response_model=AnnotatedImage)
async def get_annotated_image(
    annotated_image_id: int, session=Depends(get_session)
) -> AnnotatedImage:
    image = await session.get(AnnotatedImage, annotated_image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Annotated image not found")

    return image


@router.post("/", response_model=Annotation)
async def create_annotation(
    data: AnnotationCreate, session=Depends(get_session)
) -> Annotation:
    image = await session.get(AnnotatedImage, data.annotated_image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    annotation = Annotation(
        annotated_image_id=data.annotated_image_id,
        polygon=data.polygon,
        damage_level=data.damage_level,
    )

    session.add(annotation)
    await session.commit()
    await session.refresh(annotation)

    return annotation


@router.get("/{annotation_id}", response_model=Annotation)
async def get_annotation(
    annotation_id: int, session=Depends(get_session)
) -> Annotation:
    annotation = await session.get(Annotation, annotation_id)
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")

    return annotation


@router.put("/{annotation_id}", response_model=Annotation)
async def update_annotation(
    annotation_id: int,
    data: AnnotationUpdate,
    session=Depends(get_session),
) -> Annotation:
    annotation = await session.get(Annotation, annotation_id)
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")

    annotation.polygon = data.polygon
    annotation.damage_level = data.damage_level

    session.add(annotation)
    await session.commit()
    await session.refresh(annotation)

    return annotation
