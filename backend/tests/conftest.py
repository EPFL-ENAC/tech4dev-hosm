import os
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import ASGITransport, AsyncClient
from unittest.mock import patch, PropertyMock


@pytest.fixture
async def client():
    from api.config import config

    with (
        patch.object(type(config), "DB_URL", new_callable=PropertyMock) as mock_db_url,
        patch.object(config, "CODES_ANNOTATORS", ["test-annotator-code"]),
        patch.object(config, "CODES_REVIEWERS", ["test-reviewer-code"]),
    ):
        mock_db_url.return_value = "sqlite+aiosqlite:///:memory:"

        from api.main import app
        from api.db import create_db_and_tables

        await create_db_and_tables()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": "Bearer test-reviewer-code"},
        ) as client:
            yield client


@pytest.fixture
async def test_user(client):
    from sqlmodel import select
    from api.db import engine
    from api.models.annotations import User as TestUser

    async with AsyncSession(engine) as session:
        user = TestUser(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            is_reviewer=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


@pytest.fixture
async def test_annotated_image(test_user, client):
    from api.db import engine
    from api.models.annotations import AnnotatedImage as TestAnnotatedImage

    async with AsyncSession(engine) as session:
        image = TestAnnotatedImage(
            image_path="http://example.com/image.jpg",
            annotator_id=test_user.id,
        )
        session.add(image)
        await session.commit()
        await session.refresh(image)
    return image


@pytest.fixture
async def test_annotation(test_annotated_image, client):
    from api.db import engine
    from api.models.annotations import Annotation as TestAnnotation

    async with AsyncSession(engine) as session:
        annotation = TestAnnotation(
            annotated_image_id=test_annotated_image.id,
            polygon=[[0.0, 0.0], [1.0, 1.0], [2.0, 0.0]],
            damage_level=1,
        )
        session.add(annotation)
        await session.commit()
        await session.refresh(annotation)
    return annotation
