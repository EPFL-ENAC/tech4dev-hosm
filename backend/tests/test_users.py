import pytest

from api.models.annotations import AnnotatedImage
from api.services.annotations import get_annotating_seconds_by_annotator


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
    assert "non_reviewed_images_count" in user
    assert "total_annotations_count" in user
    assert user["annotated_images_count"] >= 0
    assert user["non_reviewed_images_count"] >= 0
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
async def test_get_users_sort_by_non_reviewed_images_count(client, test_user):
    """Test sorting by non_reviewed_images_count."""
    response = await client.get(
        "/annotations/users/?sort_by=non_reviewed_images_count&sort_order=desc"
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
        assert "non_reviewed_images_count" in user
        assert "total_annotations_count" in user


@pytest.mark.asyncio
async def test_download_users_csv(client, test_user):
    """Test that reviewers can download users as CSV."""
    response = await client.get("/annotations/download-users-csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    assert "users.csv" in response.headers["content-disposition"]

    content = response.text
    assert "Name" in content
    assert "Email" in content
    assert "Role" in content
    assert "Time Spent (minutes)" in content
    assert "Total Annotations" in content
    # The test user should be present in the CSV
    assert "Test User" in content


@pytest.mark.asyncio
async def test_download_users_csv_email_masked(client, test_user):
    """Test that emails are masked in the CSV export."""
    response = await client.get("/annotations/download-users-csv")
    assert response.status_code == 200

    content = response.text
    # Raw email must not appear in the CSV
    assert "test@example.com" not in content
    # Masked version: first letter of each part followed by ***
    assert "t***@e***.c***" in content


@pytest.mark.asyncio
async def test_download_users_csv_non_reviewer_forbidden(client_non_reviewer):
    """Test that non-reviewer users cannot download the CSV."""
    response = await client_non_reviewer.get("/annotations/download-users-csv")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_users_includes_annotation_time_seconds(
    client, test_annotated_image, test_annotation
):
    """Test that the users endpoint returns annotation_time_seconds."""
    response = await client.get("/annotations/users/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    for user in data["items"]:
        assert "annotation_time_seconds" in user
        assert user["annotation_time_seconds"] >= 0


async def _seed_image_with_annotations(
    session, annotator_id, created_at_values, updated_at_values
):
    """Create one image with annotations at explicit timestamps.

    ``updated_at_values`` holds one entry per annotation; pass None for
    never-updated annotations so the ORM does not stamp the current time.
    """
    from api.models.annotations import Annotation, DamageLevel

    image = AnnotatedImage(
        image_path=f"sql-test/{annotator_id}/{created_at_values[0].isoformat()}.jpg",
        annotator_id=annotator_id,
    )
    session.add(image)
    await session.flush()
    image_id = image.id

    for created_at, updated_at in zip(created_at_values, updated_at_values):
        session.add(
            Annotation(
                annotated_image_id=image_id,
                polygon=[[0.0, 0.0], [1.0, 1.0], [2.0, 0.0]],
                damage_level=DamageLevel.UNDAMAGED,
                created_at=created_at,
                updated_at=updated_at,
            )
        )
    await session.commit()
    return image_id


@pytest.mark.asyncio
async def test_annotating_seconds_same_day(client, test_user):
    """Two annotations on the same day: span between first and last."""
    from datetime import datetime, timezone

    from sqlmodel.ext.asyncio.session import AsyncSession

    from api.db import get_engine

    engine = get_engine("sqlite+aiosqlite:///:memory:")
    async with AsyncSession(engine) as session:
        await _seed_image_with_annotations(
            session,
            test_user.id,
            [
                datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                datetime(2024, 1, 15, 11, 30, tzinfo=timezone.utc),
            ],
            [None, None],
        )
        result = await get_annotating_seconds_by_annotator([test_user.id], session)

    assert result == {test_user.id: 5400}


@pytest.mark.asyncio
async def test_annotating_seconds_single_annotation(client, test_user):
    """A single annotation on a day yields zero time."""
    from datetime import datetime, timezone

    from sqlmodel.ext.asyncio.session import AsyncSession

    from api.db import get_engine

    engine = get_engine("sqlite+aiosqlite:///:memory:")
    async with AsyncSession(engine) as session:
        await _seed_image_with_annotations(
            session,
            test_user.id,
            [datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)],
            [None],
        )
        result = await get_annotating_seconds_by_annotator([test_user.id], session)

    assert result == {test_user.id: 0}


@pytest.mark.asyncio
async def test_annotating_seconds_across_days(client, test_user):
    """Annotations on two days: single-annotation days contribute zero."""
    from datetime import datetime, timezone

    from sqlmodel.ext.asyncio.session import AsyncSession

    from api.db import get_engine

    engine = get_engine("sqlite+aiosqlite:///:memory:")
    async with AsyncSession(engine) as session:
        await _seed_image_with_annotations(
            session,
            test_user.id,
            [
                datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
                datetime(2024, 1, 16, 8, 0, tzinfo=timezone.utc),
            ],
            [None, None, None],
        )
        result = await get_annotating_seconds_by_annotator([test_user.id], session)

    assert result == {test_user.id: 7200}


@pytest.mark.asyncio
async def test_annotating_seconds_updated_at_priority(client, test_user):
    """updated_at is used over created_at: effective span is 09:10 to 09:20."""
    from datetime import datetime, timezone

    from sqlmodel.ext.asyncio.session import AsyncSession

    from api.db import get_engine

    engine = get_engine("sqlite+aiosqlite:///:memory:")
    async with AsyncSession(engine) as session:
        await _seed_image_with_annotations(
            session,
            test_user.id,
            [
                datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
                datetime(2024, 1, 15, 9, 20, tzinfo=timezone.utc),
            ],
            [datetime(2024, 1, 15, 9, 10, tzinfo=timezone.utc), None],
        )
        result = await get_annotating_seconds_by_annotator([test_user.id], session)

    assert result == {test_user.id: 600}


@pytest.mark.asyncio
async def test_annotating_seconds_same_second(client, test_user):
    """Two annotations on the same second of a day: zero span."""
    from datetime import datetime, timezone

    from sqlmodel.ext.asyncio.session import AsyncSession

    from api.db import get_engine

    engine = get_engine("sqlite+aiosqlite:///:memory:")
    async with AsyncSession(engine) as session:
        await _seed_image_with_annotations(
            session,
            test_user.id,
            [
                datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
                datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            ],
            [None, None],
        )
        result = await get_annotating_seconds_by_annotator([test_user.id], session)

    assert result == {test_user.id: 0}


@pytest.mark.asyncio
async def test_annotating_seconds_multiple_annotators(client, test_user):
    """Each annotator only counts the time of their own images."""
    from datetime import datetime, timezone

    from sqlmodel.ext.asyncio.session import AsyncSession

    from api.db import get_engine
    from api.models.annotations import User

    engine = get_engine("sqlite+aiosqlite:///:memory:")
    async with AsyncSession(engine) as session:
        other_user = User(
            email="other@example.com",
            full_name="Other Annotator",
            is_reviewer=False,
        )
        session.add(other_user)
        await session.flush()
        other_user_id = other_user.id

        await _seed_image_with_annotations(
            session,
            test_user.id,
            [
                datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                datetime(2024, 1, 15, 11, 30, tzinfo=timezone.utc),
            ],
            [None, None],
        )
        await _seed_image_with_annotations(
            session,
            other_user_id,
            [
                datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
                datetime(2024, 1, 15, 9, 20, tzinfo=timezone.utc),
            ],
            [datetime(2024, 1, 15, 9, 10, tzinfo=timezone.utc), None],
        )
        result = await get_annotating_seconds_by_annotator(
            [test_user.id, other_user_id], session
        )

    assert result == {test_user.id: 5400, other_user_id: 600}


@pytest.mark.asyncio
async def test_annotating_seconds_empty_ids(client, test_user):
    """An empty annotator id list yields an empty result."""
    from sqlmodel.ext.asyncio.session import AsyncSession

    from api.db import get_engine

    engine = get_engine("sqlite+aiosqlite:///:memory:")
    async with AsyncSession(engine) as session:
        result = await get_annotating_seconds_by_annotator([], session)

    assert result == {}


@pytest.mark.asyncio
async def test_annotation_time_nonzero_in_users_and_csv(
    client, test_user, test_annotated_image, test_annotation
):
    """Same-day annotations yield 90 minutes in /users/ and in the CSV.

    The first annotation is created 10:00 and updated 11:30 (updated_at takes
    priority), the second is created 10:00: span 10:00 -> 11:30 = 5400 s.
    """
    from datetime import datetime, timezone

    from sqlmodel.ext.asyncio.session import AsyncSession

    from api.db import get_engine
    from api.models.annotations import Annotation as TestAnnotation
    from api.models.annotations import DamageLevel

    engine = get_engine("sqlite+aiosqlite:///:memory:")
    async with AsyncSession(engine) as session:
        first = await session.get(TestAnnotation, test_annotation.id)
        assert first is not None
        # Set updated_at explicitly: any UPDATE would otherwise trigger the
        # column's onupdate and stamp "now" as the effective timestamp.
        first.created_at = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
        first.updated_at = datetime(2024, 1, 15, 11, 30, tzinfo=timezone.utc)
        session.add(first)
        session.add(
            TestAnnotation(
                annotated_image_id=test_annotated_image.id,
                polygon=[[0.0, 0.0], [1.0, 1.0], [2.0, 0.0]],
                damage_level=DamageLevel.DAMAGED,
                created_at=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            )
        )
        await session.commit()

    # Users endpoint: 10:00 -> 11:30 on the same day = 5400 seconds.
    response = await client.get("/annotations/users/")
    assert response.status_code == 200
    items = response.json()["items"]
    user = next(item for item in items if item["id"] == test_user.id)
    assert user["annotation_time_seconds"] == 5400

    # CSV export: 5400 seconds = 90 minutes, column after "Last Action".
    response = await client.get("/annotations/download-users-csv")
    assert response.status_code == 200
    row = next(
        line for line in response.text.splitlines() if line.startswith("Test User,")
    )
    assert row.split(",")[5] == "90"
