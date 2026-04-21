from datetime import datetime
from enum import Enum
from typing import Annotated

from sqlalchemy import Column, DateTime, func
from sqlalchemy.types import JSON
from sqlmodel import Field, Relationship, SQLModel

Point = Annotated[list[float], Field(min_length=2, max_length=2)]


class ValidationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    email: str = Field(unique=True, index=True)
    first_name: str
    last_name: str
    is_reviewer: bool = False

    annotated_images: list["AnnotatedImage"] = Relationship(back_populates="annotator")


class UserCreate(SQLModel):
    email: str
    first_name: str
    last_name: str
    is_reviewer: bool = False


class AnnotatedImage(SQLModel, table=True):
    __tablename__ = "annotated_image"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )
    image_path: str
    validation_status: ValidationStatus = Field(default=ValidationStatus.PENDING)
    completed: bool = Field(default=False)

    annotator_id: int | None = Field(foreign_key="user.id")
    annotator: User | None = Relationship(back_populates="annotated_images")

    annotations: list["Annotation"] = Relationship(
        back_populates="image", sa_relationship_kwargs={"lazy": "selectin"}
    )


class AnnotatedImageCreate(SQLModel):
    image_path: str


class AnnotatedImageUpdate(SQLModel):
    completed: bool | None = None


class AnnotatedImageRead(SQLModel):
    id: int
    image_path: str
    validation_status: ValidationStatus
    completed: bool = False
    annotator_id: int | None = None
    annotations: list["AnnotationRead"] = []


class Annotation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )
    polygon: list[Point] = Field(sa_column=Column(JSON))
    damage_level: int = Field(ge=0, le=2)

    annotated_image_id: int | None = Field(foreign_key="annotated_image.id")
    image: AnnotatedImage | None = Relationship(back_populates="annotations")


class AnnotationCreate(SQLModel):
    annotated_image_id: int
    polygon: list[Point]
    damage_level: int = Field(ge=0, le=2)


class AnnotationUpdate(SQLModel):
    polygon: list[Point] | None = None
    damage_level: int | None = Field(default=None, ge=0, le=2)


class AnnotationRead(SQLModel):
    id: int
    polygon: list[Point]
    damage_level: int
    annotated_image_id: int | None = None
