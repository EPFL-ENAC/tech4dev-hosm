import pytest
from sqlmodel.ext.asyncio.session import AsyncSession
from httpx import ASGITransport, AsyncClient
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
        damage_level="damaged",
    )
    response = await client.post("/annotations/", json=annotation_data.model_dump())
    assert response.status_code == 200
    data = response.json()
    assert data["annotated_image_id"] == test_annotated_image.id
    assert data["damage_level"] == "damaged"


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
        damage_level="unset",
    )
    response = await client.put(
        f"/annotations/{test_annotation.id}", json=update_data.model_dump()
    )
    assert response.status_code == 200
    data = response.json()
    assert data["damage_level"] == "unset"
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
            "damage_level": "undamaged",
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
        json={"damage_level": "damaged"},
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


@pytest.mark.asyncio
async def test_approve_annotated_image(client, test_annotated_image):
    """Test that a reviewer can approve an annotated image."""
    from sqlmodel import select
    from api.db import get_engine
    from api.models.annotations import AnnotatedImage as TestAnnotatedImage, ValidationStatus

    response = await client.post(
        f"/annotations/annotated-images/{test_annotated_image.id}/approve"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["validation_status"] == "approved"
    assert data["reviewer_id"] == test_annotated_image.annotator_id  # test_user is a reviewer
    assert data["reviewed_at"] is not None

    # Verify in database
    engine = get_engine(TEST_DB_URL)
    async with AsyncSession(engine) as session:
        image = (await session.exec(select(TestAnnotatedImage).where(TestAnnotatedImage.id == test_annotated_image.id))).first()
        assert image.validation_status == ValidationStatus.APPROVED
        assert image.reviewer_id is not None
        assert image.reviewed_at is not None


@pytest.mark.asyncio
async def test_reject_annotated_image(client, test_annotated_image):
    """Test that a reviewer can reject an annotated image."""
    from sqlmodel import select
    from api.db import get_engine
    from api.models.annotations import AnnotatedImage as TestAnnotatedImage, ValidationStatus

    response = await client.post(
        f"/annotations/annotated-images/{test_annotated_image.id}/reject"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["validation_status"] == "rejected"
    assert data["reviewer_id"] == test_annotated_image.annotator_id  # test_user is a reviewer
    assert data["reviewed_at"] is not None

    # Verify in database
    engine = get_engine(TEST_DB_URL)
    async with AsyncSession(engine) as session:
        image = (await session.exec(select(TestAnnotatedImage).where(TestAnnotatedImage.id == test_annotated_image.id))).first()
        assert image.validation_status == ValidationStatus.REJECTED
        assert image.reviewer_id is not None
        assert image.reviewed_at is not None


@pytest.mark.asyncio
async def test_approve_reject_nonexistent_image(client, test_user):
    """Test that approving/rejecting a non-existent image returns 404."""
    from api.services.auth import create_jwt_token
    from api.main import app

    # Get a fresh token
    access_token = await create_jwt_token(test_user)

    # Use a new client with fresh token
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {access_token}"},
    ) as fresh_client:
        response = await fresh_client.post("/annotations/annotated-images/99999/approve")
        assert response.status_code == 404
        assert response.json()["detail"] == "Annotated image not found"

        response = await fresh_client.post("/annotations/annotated-images/99999/reject")
        assert response.status_code == 404
        assert response.json()["detail"] == "Annotated image not found"


@pytest.mark.asyncio
async def test_non_reviewer_cannot_approve_reject(client_non_reviewer, test_annotated_image):
    """Test that a non-reviewer cannot approve or reject images."""
    response = await client_non_reviewer.post(
        f"/annotations/annotated-images/{test_annotated_image.id}/approve"
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Access denied: reviewers only"

    response = await client_non_reviewer.post(
        f"/annotations/annotated-images/{test_annotated_image.id}/reject"
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Access denied: reviewers only"


@pytest.mark.asyncio
async def test_last_action_at_updated_on_approve(client, test_user, test_annotated_image):
    """Test that last_action_at is updated when user approves an image."""
    from datetime import datetime
    from sqlmodel import select
    from api.db import get_engine
    from api.models.annotations import User as TestUser

    # Get initial last_action_at
    engine = get_engine(TEST_DB_URL)
    async with AsyncSession(engine) as session:
        user = (await session.exec(select(TestUser).where(TestUser.id == test_user.id))).first()
        initial_last_action_at = user.last_action_at

    # Approve the image via API
    response = await client.post(
        f"/annotations/annotated-images/{test_annotated_image.id}/approve"
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
async def test_last_action_at_updated_on_reject(client, test_user, test_annotated_image):
    """Test that last_action_at is updated when user rejects an image."""
    from datetime import datetime
    from sqlmodel import select
    from api.db import get_engine
    from api.models.annotations import User as TestUser

    # Get initial last_action_at
    engine = get_engine(TEST_DB_URL)
    async with AsyncSession(engine) as session:
        user = (await session.exec(select(TestUser).where(TestUser.id == test_user.id))).first()
        initial_last_action_at = user.last_action_at

    # Reject the image via API
    response = await client.post(
        f"/annotations/annotated-images/{test_annotated_image.id}/reject"
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
async def test_reviewer_can_get_annotated_images_by_annotator_id(client, test_user):
    """Test that a reviewer can fetch annotated images for a specific annotator."""
    response = await client.get(
        f"/annotations/annotated-images/?annotator_id={test_user.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_non_reviewer_cannot_get_annotated_images_by_annotator_id(client_non_reviewer):
    """Test that a non-reviewer cannot fetch annotated images for another annotator."""
    response = await client_non_reviewer.get(
        "/annotations/annotated-images/?annotator_id=999"
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Access denied: reviewers only"
