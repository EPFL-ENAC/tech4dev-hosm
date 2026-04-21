import pytest
from api.models.annotations import (
    UserCreate,
    AnnotatedImageCreate,
    AnnotationCreate,
    AnnotationUpdate,
)


@pytest.mark.asyncio
async def test_get_user(client, test_user):
    response = await client.get(f"/annotations/users/{test_user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email


@pytest.mark.asyncio
async def test_create_annotated_image(client, test_user):
    image_data = AnnotatedImageCreate(
        image_path="http://example.com/new-image.jpg",
        annotator_id=test_user.id,
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
