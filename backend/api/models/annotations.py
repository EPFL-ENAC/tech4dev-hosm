from datetime import datetime
from enum import Enum
from typing import Annotated

from sqlalchemy import Column, DateTime, UniqueConstraint, func
from sqlalchemy.types import JSON
from sqlmodel import Field, Relationship, SQLModel

Point = Annotated[list[float], Field(min_length=2, max_length=2)]


class ValidationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class DamageLevel(str, Enum):
    UNSET = "unset"
    UNDAMAGED = "undamaged"
    DAMAGED = "damaged"


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    last_action_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    email: str = Field(unique=True, index=True)
    full_name: str
    is_reviewer: bool = False

    annotated_images: list["AnnotatedImage"] = Relationship(
        back_populates="annotator",
        sa_relationship_kwargs={"foreign_keys": "AnnotatedImage.annotator_id"},
    )
    reviewed_images: list["AnnotatedImage"] = Relationship(
        back_populates="reviewer",
        sa_relationship_kwargs={"foreign_keys": "AnnotatedImage.reviewer_id"},
    )


class UserCreate(SQLModel):
    email: str
    full_name: str
    is_reviewer: bool = False


class AnnotatedImage(SQLModel, table=True):
    __tablename__ = "annotated_image"
    __table_args__ = (
        UniqueConstraint("image_path", "annotator_id", name="uq_image_path_annotator"),
    )
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )
    reviewed_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    image_path: str = Field(index=True)  # Index for filtering by image path
    validation_status: ValidationStatus = Field(
        default=ValidationStatus.PENDING, sa_column_kwargs={"index": True}
    )  # Index for filtering by validation status
    completed: bool = Field(default=False)

    annotator_id: int = Field(
        foreign_key="user.id", sa_column_kwargs={"index": True}
    )  # Index for filtering by annotator
    annotator: User | None = Relationship(
        back_populates="annotated_images",
        sa_relationship_kwargs={"foreign_keys": "AnnotatedImage.annotator_id"},
    )
    reviewer_id: int | None = Field(
        default=None, foreign_key="user.id", sa_column_kwargs={"index": True}
    )  # Index for filtering by reviewer
    reviewer: User | None = Relationship(
        back_populates="reviewed_images",
        sa_relationship_kwargs={"foreign_keys": "AnnotatedImage.reviewer_id"},
    )

    annotations: list["Annotation"] = Relationship(
        back_populates="image",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"},
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
    reviewer_id: int | None = None
    reviewed_at: datetime | None = None
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
    damage_level: DamageLevel = Field(default=DamageLevel.UNSET)

    annotated_image_id: int = Field(foreign_key="annotated_image.id")
    image: AnnotatedImage | None = Relationship(back_populates="annotations")


class AnnotationCreate(SQLModel):
    annotated_image_id: int
    polygon: list[Point]
    damage_level: DamageLevel = Field(default=DamageLevel.UNSET)


class AnnotationUpdate(SQLModel):
    polygon: list[Point] | None = None
    damage_level: DamageLevel | None = None


class AnnotationRead(SQLModel):
    id: int
    polygon: list[Point]
    damage_level: DamageLevel
    annotated_image_id: int | None = None


class UserReadWithStats(SQLModel):
    id: int
    email: str
    full_name: str
    is_reviewer: bool
    created_at: datetime
    last_action_at: datetime | None = None
    annotated_images_count: int
    non_reviewed_images_count: int
    total_annotations_count: int


class UserListResponse(SQLModel):
    items: list[UserReadWithStats]
    total: int
    page: int
    page_size: int
    total_pages: int
