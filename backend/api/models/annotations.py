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
    email: str
    first_name: str
    last_name: str
    is_reviewer: bool = False

    annotated_images: list["AnnotatedImage"] = Relationship(back_populates="annotator")


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
    image_url: str
    validation_status: ValidationStatus = Field(default=ValidationStatus.PENDING)

    annotator_id: int | None = Field(foreign_key="user.id")
    annotator: User | None = Relationship(back_populates="annotated_images")

    annotations: list["Annotation"] = Relationship(back_populates="image")


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

    image_id: int | None = Field(foreign_key="annotated_image.id")
    image: AnnotatedImage | None = Relationship(back_populates="annotations")
