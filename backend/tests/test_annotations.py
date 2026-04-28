import pytest
from sqlmodel.ext.asyncio.session import AsyncSession
from tests.conftest import TEST_DB_URL

from api.models.annotations import (
    AnnotatedImageCreate,
    AnnotationCreate,
    AnnotationUpdate,
)


@pytest.mark.asyncio
async def test_create_annotated_image(client, test_user):
    image_data = AnnotatedImageCreate(
        image_path="http://example.com/new-image.jpg",
    )
    response = await client.post(
        "/annotations/annotated-images/", json=image_data.model_dump()
    )
    assert response.status_code == 200
    data = response.json()
    assert data["image_path"] == "http://example.com/new-image.jpg"
    assert data["annotator_id"] == test_user.id


@pytest.mark.asyncio
async def test_get_annotated_image(client, test_annotated_image):
    response = await client.get(
        f"/annotations/annotated-images/{test_annotated_image.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_annotated_image.id
    assert data["image_path"] == test_annotated_image.image_path


@pytest.mark.asyncio
async def test_get_annotated_images(client, test_annotated_image):
    response = await client.get("/annotations/annotated-images/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    image_ids = [img["id"] for img in data]
    assert test_annotated_image.id in image_ids


@pytest.mark.asyncio
async def test_create_annotation(client, test_annotated_image):
    annotation_data = AnnotationCreate(
        annotated_image_id=test_annotated_image.id,
        polygon=[[0.0, 0.0], [1.0, 1.0], [2.0, 0.0]],
        damage_level=2,
    )
    response = await client.post("/annotations/", json=annotation_data.model_dump())
    assert response.status_code == 200
    data = response.json()
    assert data["annotated_image_id"] == test_annotated_image.id
    assert data["damage_level"] == 2


@pytest.mark.asyncio
async def test_get_annotation(client, test_annotation):
    response = await client.get(f"/annotations/{test_annotation.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_annotation.id
    assert data["damage_level"] == test_annotation.damage_level


@pytest.mark.asyncio
async def test_update_annotation(client, test_annotation):
    update_data = AnnotationUpdate(
        polygon=[[0.0, 0.0], [2.0, 2.0], [3.0, 0.0]],
        damage_level=0,
    )
    response = await client.put(
        f"/annotations/{test_annotation.id}", json=update_data.model_dump()
    )
    assert response.status_code == 200
    data = response.json()
    assert data["damage_level"] == 0
    assert data["polygon"] == [[0.0, 0.0], [2.0, 2.0], [3.0, 0.0]]


@pytest.mark.asyncio
async def test_delete_annotation(client, test_annotation):
    response = await client.delete(f"/annotations/{test_annotation.id}")
    assert response.status_code == 204

    response = await client.get(f"/annotations/{test_annotation.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_annotated_image(client, test_annotated_image):
    response = await client.delete(
        f"/annotations/annotated-images/{test_annotated_image.id}"
    )
    assert response.status_code == 204

    response = await client.get(
        f"/annotations/annotated-images/{test_annotated_image.id}"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_last_action_at_updated_on_create_image(client, test_user):
    """Test that last_action_at is updated when user creates an image."""
    from datetime import datetime
    from sqlmodel import select
    from api.db import get_engine
    from api.models.annotations import User as TestUser

    # Get initial last_action_at
    engine = get_engine(TEST_DB_URL)
    async with AsyncSession(engine) as session:
        user = (await session.exec(select(TestUser).where(TestUser.id == test_user.id))).first()
        initial_last_action_at = user.last_action_at

    # Create a new image via API
    response = await client.post(
        "/annotations/annotated-images/",
        json={"image_path": "http://example.com/new_image.jpg"},
    )
    assert response.status_code == 200

    # Check that last_action_at was updated
    async with AsyncSession(engine) as session:
        user = (await session.exec(select(TestUser).where(TestUser.id == test_user.id))).first()
        assert user.last_action_at is not None
        if initial_last_action_at:
            assert user.last_action_at > initial_last_action_at
        else:
            # First action, should be set
            assert user.last_action_at <= datetime.now()


@pytest.mark.asyncio
async def test_last_action_at_updated_on_update_image(client, test_user, test_annotated_image):
    """Test that last_action_at is updated when user updates an image."""
    from datetime import datetime
    from sqlmodel import select
    from api.db import get_engine
    from api.models.annotations import User as TestUser

    # Get initial last_action_at
    engine = get_engine(TEST_DB_URL)
    async with AsyncSession(engine) as session:
        user = (await session.exec(select(TestUser).where(TestUser.id == test_user.id))).first()
        initial_last_action_at = user.last_action_at

    # Update the image via API
    response = await client.put(
        f"/annotations/annotated-images/{test_annotated_image.id}",
        json={"completed": True},
    )
    assert response.status_code == 200

    # Check that last_action_at was updated
    async with AsyncSession(engine) as session:
        user = (await session.exec(select(TestUser).where(TestUser.id == test_user.id))).first()
        assert user.last_action_at is not None
        if initial_last_action_at:
            assert user.last_action_at > initial_last_action_at
        else:
            assert user.last_action_at <= datetime.now()


@pytest.mark.asyncio
async def test_last_action_at_updated_on_delete_image(client, test_user, test_annotated_image):
    """Test that last_action_at is updated when user deletes an image."""
    from datetime import datetime
    from sqlmodel import select
    from api.db import get_engine
    from api.models.annotations import User as TestUser

    # Get initial last_action_at
    engine = get_engine(TEST_DB_URL)
    async with AsyncSession(engine) as session:
        user = (await session.exec(select(TestUser).where(TestUser.id == test_user.id))).first()
        initial_last_action_at = user.last_action_at

    # Delete the image via API
    response = await client.delete(f"/annotations/annotated-images/{test_annotated_image.id}")
    assert response.status_code == 204

    # Check that last_action_at was updated
    async with AsyncSession(engine) as session:
        user = (await session.exec(select(TestUser).where(TestUser.id == test_user.id))).first()
        assert user.last_action_at is not None
        if initial_last_action_at:
            assert user.last_action_at > initial_last_action_at
        else:
            assert user.last_action_at <= datetime.now()


@pytest.mark.asyncio
async def test_last_action_at_updated_on_create_annotation(client, test_user, test_annotated_image):
    """Test that last_action_at is updated when user creates an annotation."""
    from datetime import datetime
    from sqlmodel import select
    from api.db import get_engine
    from api.models.annotations import User as TestUser

    # Get initial last_action_at
    engine = get_engine(TEST_DB_URL)
    async with AsyncSession(engine) as session:
        user = (await session.exec(select(TestUser).where(TestUser.id == test_user.id))).first()
        initial_last_action_at = user.last_action_at

    # Create a new annotation via API
    response = await client.post(
        "/annotations/",
        json={
            "annotated_image_id": test_annotated_image.id,
            "polygon": [[0.0, 0.0], [1.0, 1.0], [2.0, 0.0]],
            "damage_level": 1,
        },
    )
    assert response.status_code == 200

    # Check that last_action_at was updated
    async with AsyncSession(engine) as session:
        user = (await session.exec(select(TestUser).where(TestUser.id == test_user.id))).first()
        assert user.last_action_at is not None
        if initial_last_action_at:
            assert user.last_action_at > initial_last_action_at
        else:
            assert user.last_action_at <= datetime.now()


@pytest.mark.asyncio
async def test_last_action_at_updated_on_update_annotation(
    client, test_user, test_annotated_image, test_annotation
):
    """Test that last_action_at is updated when user updates an annotation."""
    from datetime import datetime
    from sqlmodel import select
    from api.db import get_engine
    from api.models.annotations import User as TestUser

    # Get initial last_action_at
    engine = get_engine(TEST_DB_URL)
    async with AsyncSession(engine) as session:
        user = (await session.exec(select(TestUser).where(TestUser.id == test_user.id))).first()
        initial_last_action_at = user.last_action_at

    # Update the annotation via API
    response = await client.put(
        f"/annotations/{test_annotation.id}",
        json={"damage_level": 2},
    )
    assert response.status_code == 200

    # Check that last_action_at was updated
    async with AsyncSession(engine) as session:
        user = (await session.exec(select(TestUser).where(TestUser.id == test_user.id))).first()
        assert user.last_action_at is not None
        if initial_last_action_at:
            assert user.last_action_at > initial_last_action_at
        else:
            assert user.last_action_at <= datetime.now()


@pytest.mark.asyncio
async def test_last_action_at_updated_on_delete_annotation(
    client, test_user, test_annotated_image, test_annotation
):
    """Test that last_action_at is updated when user deletes an annotation."""
    from datetime import datetime
    from sqlmodel import select
    from api.db import get_engine
    from api.models.annotations import User as TestUser

    # Get initial last_action_at
    engine = get_engine(TEST_DB_URL)
    async with AsyncSession(engine) as session:
        user = (await session.exec(select(TestUser).where(TestUser.id == test_user.id))).first()
        initial_last_action_at = user.last_action_at

    # Delete the annotation via API
    response = await client.delete(f"/annotations/{test_annotation.id}")
    assert response.status_code == 204

    # Check that last_action_at was updated
    async with AsyncSession(engine) as session:
        user = (await session.exec(select(TestUser).where(TestUser.id == test_user.id))).first()
        assert user.last_action_at is not None
        if initial_last_action_at:
            assert user.last_action_at > initial_last_action_at
        else:
            assert user.last_action_at <= datetime.now()


@pytest.mark.asyncio
async def test_last_action_at_not_updated_on_read_operations(client, test_user):
    """Test that last_action_at is NOT updated on read operations."""
    from datetime import datetime
    from sqlmodel import select
    from api.db import get_engine
    from api.models.annotations import User as TestUser

    engine = get_engine(TEST_DB_URL)

    # Get initial last_action_at
    async with AsyncSession(engine) as session:
        user = (await session.exec(select(TestUser).where(TestUser.id == test_user.id))).first()
        initial_last_action_at = user.last_action_at

    # Perform read operations
    await client.get("/annotations/users/")  # Get users
    await client.get("/annotations/annotated-images/")  # Get images

    # Small delay to ensure time difference if updated
    import asyncio
    await asyncio.sleep(0.1)

    # Check that last_action_at was NOT updated
    async with AsyncSession(engine) as session:
        user = (await session.exec(select(TestUser).where(TestUser.id == test_user.id))).first()
        # last_action_at should remain the same (or still be None if it was None)
        if initial_last_action_at:
            assert user.last_action_at == initial_last_action_at
