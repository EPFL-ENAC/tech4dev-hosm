import os

import pytest
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from httpx import ASGITransport, AsyncClient


USER_DICT = {
    "email": "test@example.com",
    "full_name": "Test User",
    "is_reviewer": True,
}

NON_REVIEWER_USER_DICT = {
    "email": "nonreviewer@example.com",
    "full_name": "Non Reviewer",
    "is_reviewer": False,
}

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
def setup_test_env():
    """Set up test environment variables."""
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["CODES_ANNOTATORS"] = '["test-annotator-code"]'
    os.environ["CODES_REVIEWERS"] = '["test-reviewer-code"]'
    os.environ["DB_HOST"] = "localhost"
    os.environ["DB_NAME"] = "test_db"
    os.environ["DB_USER"] = "test_user"
    os.environ["DB_PASSWORD"] = "test_password"


@pytest.fixture
async def client(setup_test_env):
    from fastapi_cache import FastAPICache
    from fastapi_cache.backends.inmemory import InMemoryBackend

    # Initialize cache for tests
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache-test")

    from api.main import app
    from api.db import get_engine, create_db_and_tables
    from api.services.auth import create_jwt_token
    from api.models.annotations import User as TestUser

    engine = get_engine(TEST_DB_URL)

    access_token = await create_jwt_token(TestUser(**USER_DICT))

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await create_db_and_tables(TEST_DB_URL)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {access_token}"},
    ) as client:
        yield client


@pytest.fixture
async def test_user(client):
    from sqlmodel import select
    from api.db import get_engine
    from api.models.annotations import User as TestUser

    engine = get_engine(TEST_DB_URL)
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
    from api.db import get_engine
    from api.models.annotations import AnnotatedImage as TestAnnotatedImage

    engine = get_engine(TEST_DB_URL)
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
    from api.db import get_engine
    from api.models.annotations import Annotation as TestAnnotation

    engine = get_engine(TEST_DB_URL)
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


@pytest.fixture
async def client_non_reviewer(client, test_user):
    """Create a client authenticated as a non-reviewer user."""
    from httpx import ASGITransport, AsyncClient
    from sqlmodel import select

    from api.db import get_engine
    from api.main import app
    from api.models.annotations import User as TestUser
    from api.services.auth import create_jwt_token

    engine = get_engine(TEST_DB_URL)
    async with AsyncSession(engine) as session:
        non_reviewer = (
            await session.exec(
                select(TestUser).where(
                    TestUser.email == NON_REVIEWER_USER_DICT["email"]
                )
            )
        ).first()
        if not non_reviewer:
            non_reviewer = TestUser(**NON_REVIEWER_USER_DICT)
            session.add(non_reviewer)
            await session.commit()
            await session.refresh(non_reviewer)

    access_token = await create_jwt_token(non_reviewer)

    # Create a new client with non-reviewer token instead of modifying shared client
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {access_token}"},
    ) as non_reviewer_client:
        yield non_reviewer_client
