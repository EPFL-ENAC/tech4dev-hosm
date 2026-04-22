import pytest
from sqlmodel.ext.asyncio.session import AsyncSession
from httpx import ASGITransport, AsyncClient
from unittest.mock import patch, PropertyMock


USER_DICT = {
    "email": "test@example.com",
    "full_name": "Test User",
    "is_reviewer": True,
}


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
        from api.services.auth import create_jwt_token
        from api.models.annotations import User as TestUser

        access_token = await create_jwt_token(TestUser(**USER_DICT))

        await create_db_and_tables()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {access_token}"},
        ) as client:
            yield client


@pytest.fixture
async def test_user(client):
    from sqlmodel import select
    from api.db import engine
    from api.models.annotations import User as TestUser

    async with AsyncSession(engine) as session:
        user = (
            await session.exec(
                select(TestUser).where(TestUser.email == USER_DICT["email"])
            )
        ).first()
        if user:
            return user

        user = TestUser(**USER_DICT)
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
