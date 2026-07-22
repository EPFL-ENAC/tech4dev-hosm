from unittest.mock import patch

import pytest

from tests.conftest import TEST_DB_URL


@pytest.mark.asyncio
async def test_get_random_image_path_no_images(client, test_user):
    """Test that None is returned when no images are available."""
    with patch("api.views.images.get_all_image_paths", return_value=set()):
        response = await client.post("/images/random", json=[])

    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
async def test_get_random_image_path_all_excluded(client, test_user):
    """Test that None is returned when all images are excluded."""
    image_paths = {"dataset1/image1.jpg", "dataset1/image2.jpg"}
    with patch("api.views.images.get_all_image_paths", return_value=image_paths):
        response = await client.post(
            "/images/random",
            json=["dataset1/image1.jpg", "dataset1/image2.jpg"],
        )

    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
async def test_get_random_image_path_prefer_low_annotators(client, test_user):
    """Test prefer_low_annotators_count=True returns image with fewest annotators."""
    from sqlmodel.ext.asyncio.session import AsyncSession

    from api.db import get_engine
    from api.models.annotations import AnnotatedImage as TestAnnotatedImage
    from api.models.annotations import User as TestUser

    engine = get_engine(TEST_DB_URL)

    async with AsyncSession(engine) as session:
        other_user = TestUser(
            email="other@example.com",
            full_name="Other User",
            is_reviewer=False,
        )
        session.add(other_user)
        await session.commit()
        await session.refresh(other_user)
        assert other_user.id is not None

        # image1: 2 annotators
        session.add(
            TestAnnotatedImage(
                image_path="dataset1/image1.jpg", annotator_id=test_user.id
            )
        )
        session.add(
            TestAnnotatedImage(
                image_path="dataset1/image1.jpg", annotator_id=other_user.id
            )
        )
        # image2: 1 annotator
        session.add(
            TestAnnotatedImage(
                image_path="dataset1/image2.jpg", annotator_id=test_user.id
            )
        )
        await session.commit()

    image_paths = {"dataset1/image1.jpg", "dataset1/image2.jpg", "dataset1/image3.jpg"}
    with patch("api.views.images.get_all_image_paths", return_value=image_paths):
        response = await client.post(
            "/images/random",
            json=[],
            params={"prefer_low_annotators_count": "true"},
        )

    assert response.status_code == 200
    # image3 has zero annotations (never annotated) → highest priority
    assert response.json() == "dataset1/image3.jpg"


@pytest.mark.asyncio
async def test_get_random_image_path_prioritises_unannotated_image(client, test_user):
    """Test prefer_low_annotators_count=True prioritises images never annotated (0 annotators)."""
    from sqlmodel.ext.asyncio.session import AsyncSession

    from api.db import get_engine
    from api.models.annotations import AnnotatedImage as TestAnnotatedImage

    engine = get_engine(TEST_DB_URL)

    async with AsyncSession(engine) as session:
        # image1: 1 annotator (has been annotated before)
        session.add(
            TestAnnotatedImage(
                image_path="dataset1/image1.jpg", annotator_id=test_user.id
            )
        )
        await session.commit()

    image_paths = {
        "dataset1/image1.jpg",  # 1 existing annotation
        "dataset1/image2.jpg",  # never annotated → should win
    }
    with patch("api.views.images.get_all_image_paths", return_value=image_paths):
        response = await client.post(
            "/images/random",
            json=[],
            params={"prefer_low_annotators_count": "true"},
        )

    assert response.status_code == 200
    # image2 is unannotated, so it should be selected in priority over image1
    assert response.json() == "dataset1/image2.jpg"


@pytest.mark.asyncio
async def test_get_random_image_path_prefer_low_annotators_with_exclusion(
    client, test_user
):
    """Test prefer_low_annotators_count=True respects exclusions and falls back."""
    from sqlmodel.ext.asyncio.session import AsyncSession

    from api.db import get_engine
    from api.models.annotations import AnnotatedImage as TestAnnotatedImage
    from api.models.annotations import User as TestUser

    engine = get_engine(TEST_DB_URL)

    async with AsyncSession(engine) as session:
        other_user = TestUser(
            email="other2@example.com",
            full_name="Other User 2",
            is_reviewer=False,
        )
        session.add(other_user)
        await session.commit()
        await session.refresh(other_user)
        assert other_user.id is not None

        # image1: 2 annotators
        session.add(
            TestAnnotatedImage(
                image_path="dataset1/image1.jpg", annotator_id=test_user.id
            )
        )
        session.add(
            TestAnnotatedImage(
                image_path="dataset1/image1.jpg", annotator_id=other_user.id
            )
        )
        # image2: 1 annotator
        session.add(
            TestAnnotatedImage(
                image_path="dataset1/image2.jpg", annotator_id=test_user.id
            )
        )
        await session.commit()

    image_paths = {"dataset1/image1.jpg", "dataset1/image2.jpg"}
    with patch("api.views.images.get_all_image_paths", return_value=image_paths):
        response = await client.post(
            "/images/random",
            json=["dataset1/image2.jpg"],  # exclude the one with fewer annotators
            params={"prefer_low_annotators_count": "true"},
        )

    assert response.status_code == 200
    # image2 excluded; image1 is the only remaining annotated image (count=2)
    assert response.json() == "dataset1/image1.jpg"


@pytest.mark.asyncio
async def test_get_random_image_path_random_choice(client, test_user):
    """Test prefer_low_annotators_count=False returns a random image from available paths."""
    image_paths = {"dataset1/image1.jpg", "dataset1/image2.jpg"}

    with patch("api.views.images.get_all_image_paths", return_value=image_paths):
        with patch(
            "api.views.images.random.choice", return_value="dataset1/image2.jpg"
        ) as mock_choice:
            response = await client.post(
                "/images/random",
                json=["dataset1/image1.jpg"],
                params={"prefer_low_annotators_count": "false"},
            )

    assert response.status_code == 200
    assert response.json() == "dataset1/image2.jpg"
    mock_choice.assert_called_once_with(["dataset1/image2.jpg"])


@pytest.mark.asyncio
async def test_get_random_image_path_no_exclusions(client, test_user):
    """Test with no exclusions and prefer_low_annotators_count=False."""
    image_paths = {"dataset1/image1.jpg", "dataset1/image2.jpg"}

    with patch("api.views.images.get_all_image_paths", return_value=image_paths):
        with patch(
            "api.views.images.random.choice", return_value="dataset1/image1.jpg"
        ) as mock_choice:
            response = await client.post(
                "/images/random",
                json=[],
                params={"prefer_low_annotators_count": "false"},
            )

    assert response.status_code == 200
    assert response.json() == "dataset1/image1.jpg"
    mock_choice.assert_called_once()
    available = mock_choice.call_args[0][0]
    assert set(available) == image_paths


@pytest.mark.asyncio
async def test_get_random_image_path_non_reviewer_ok(client_non_reviewer):
    """Test that non-reviewer users can access the random image endpoint."""
    image_paths = {"dataset1/image1.jpg"}

    with patch("api.views.images.get_all_image_paths", return_value=image_paths):
        with patch(
            "api.views.images.random.choice", return_value="dataset1/image1.jpg"
        ):
            response = await client_non_reviewer.post(
                "/images/random",
                json=[],
                params={"prefer_low_annotators_count": "false"},
            )

    assert response.status_code == 200
    assert response.json() == "dataset1/image1.jpg"


@pytest.mark.asyncio
async def test_get_total_images_count(client, test_user):
    """Test that the total images count returns the number of image paths."""
    image_paths = {
        "dataset1/image1.jpg",
        "dataset1/image2.jpg",
        "dataset1/image3.jpg",
    }

    with patch("api.views.images.get_all_image_paths", return_value=image_paths):
        response = await client.get("/images/total-images-count")

    assert response.status_code == 200
    assert response.json() == 3
