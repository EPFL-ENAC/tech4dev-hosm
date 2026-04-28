import pytest


@pytest.mark.asyncio
async def test_get_users_basic(client, test_user):
    """Test basic retrieval of users list."""
    response = await client.get("/annotations/users/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data
    assert isinstance(data["items"], list)
    assert data["page"] == 1
    assert data["page_size"] == 20


@pytest.mark.asyncio
async def test_get_users_includes_stats(client, test_user, test_annotated_image):
    """Test that user stats are included in the response."""
    response = await client.get("/annotations/users/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    user = data["items"][0]
    assert "annotated_images_count" in user
    assert "total_annotations_count" in user
    assert user["annotated_images_count"] >= 0
    assert user["total_annotations_count"] >= 0


@pytest.mark.asyncio
async def test_get_users_pagination(client, test_user):
    """Test pagination parameters."""
    response = await client.get("/annotations/users/?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 10


@pytest.mark.asyncio
async def test_get_users_page_size(client, test_user):
    """Test that page_size limits the number of returned items."""
    response = await client.get("/annotations/users/?page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 5


@pytest.mark.asyncio
async def test_get_users_sort_by_full_name_asc(client, test_user):
    """Test sorting by full_name in ascending order."""
    response = await client.get("/annotations/users/?sort_by=full_name&sort_order=asc")
    assert response.status_code == 200
    data = response.json()
    if len(data["items"]) > 1:
        names = [user["full_name"] for user in data["items"]]
        assert names == sorted(names)


@pytest.mark.asyncio
async def test_get_users_sort_by_full_name_desc(client, test_user):
    """Test sorting by full_name in descending order."""
    response = await client.get("/annotations/users/?sort_by=full_name&sort_order=desc")
    assert response.status_code == 200
    data = response.json()
    if len(data["items"]) > 1:
        names = [user["full_name"] for user in data["items"]]
        assert names == sorted(names, reverse=True)


@pytest.mark.asyncio
async def test_get_users_sort_by_email(client, test_user):
    """Test sorting by email."""
    response = await client.get("/annotations/users/?sort_by=email&sort_order=asc")
    assert response.status_code == 200
    data = response.json()
    if len(data["items"]) > 1:
        emails = [user["email"] for user in data["items"]]
        assert emails == sorted(emails)


@pytest.mark.asyncio
async def test_get_users_sort_by_created_at(client, test_user):
    """Test sorting by created_at."""
    response = await client.get("/annotations/users/?sort_by=created_at&sort_order=asc")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_get_users_sort_by_annotated_images_count(client, test_user):
    """Test sorting by annotated_images_count."""
    response = await client.get(
        "/annotations/users/?sort_by=annotated_images_count&sort_order=desc"
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_get_users_sort_by_total_annotations_count(client, test_user):
    """Test sorting by total_annotations_count."""
    response = await client.get(
        "/annotations/users/?sort_by=total_annotations_count&sort_order=desc"
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_get_users_invalid_sort_by(client, test_user):
    """Test that invalid sort_by field returns 400."""
    response = await client.get("/annotations/users/?sort_by=invalid_field")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_get_users_invalid_sort_order(client, test_user):
    """Test that invalid sort_order returns 400."""
    response = await client.get("/annotations/users/?sort_order=invalid")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_get_users_non_reviewer_forbidden(client_non_reviewer):
    """Test that non-reviewer users cannot access the endpoint."""
    response = await client_non_reviewer.get("/annotations/users/")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_users_total_pages(client, test_user):
    """Test that total_pages is calculated correctly."""
    response = await client.get("/annotations/users/?page_size=1")
    assert response.status_code == 200
    data = response.json()
    expected_pages = data["total"] if data["total"] > 0 else 1
    assert data["total_pages"] == expected_pages


@pytest.mark.asyncio
async def test_get_users_user_fields(client, test_user):
    """Test that user objects contain all required fields."""
    response = await client.get("/annotations/users/")
    assert response.status_code == 200
    data = response.json()
    if len(data["items"]) > 0:
        user = data["items"][0]
        assert "id" in user
        assert "email" in user
        assert "full_name" in user
        assert "is_reviewer" in user
        assert "created_at" in user
        assert "last_action_at" in user
        assert "annotated_images_count" in user
        assert "total_annotations_count" in user
