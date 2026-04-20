"""
Get image urls and files.
"""

import logging
import random
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi_cache.decorator import cache

from api.config import config
from api.models.images import ImageGPSLocation, OverlapResponse
from api.services.images import (
    get_all_image_paths,
    get_best_overlap,
    get_best_overlap_with_others,
    get_image_location,
    get_image_resolution,
)

logger = logging.getLogger("uvicorn.error")
router = APIRouter()


@router.post(
    "/random",
    status_code=200,
    description="Get a random image path from the dataset (excluding specified images)",
)
async def get_random_image_path(
    excluded_image_paths: list[str] = [],
) -> str | None:
    available_image_paths = get_all_image_paths() - set(excluded_image_paths)

    if not available_image_paths:
        return None

    return random.choice(list(available_image_paths))


@router.post(
    "/next-overlap/{image_path:path}",
    status_code=200,
    description="Get the next image path that overlaps most with the given image",
)
@cache()
async def next_overlap(
    image_path: str,
    excluded_image_names: list[str] = [],
) -> OverlapResponse | None:
    overlap = await get_best_overlap(image_path, excluded_image_names)
    resolution = get_image_resolution(image_path)

    return (
        OverlapResponse(
            image_path=overlap[0],
            homography_matrix=overlap[1],
            overlap_ratio=overlap[2],
            resolution=resolution,
        )
        if overlap
        else None
    )


@router.post(
    "/best-overlap/{image_path:path}",
    status_code=200,
    description="Get the image path from a list that overlaps most with the given image",
)
@cache()
async def best_overlap(
    image_path: str,
    other_image_names: list[str],
) -> OverlapResponse | None:
    overlap = await get_best_overlap_with_others(image_path, other_image_names)
    resolution = get_image_resolution(image_path)

    return (
        OverlapResponse(
            image_path=overlap[0],
            homography_matrix=overlap[1],
            overlap_ratio=overlap[2],
            resolution=resolution,
        )
        if overlap
        else None
    )


@router.get(
    "/location/{image_path:path}",
    status_code=200,
    description="Get the GPS location of an image from its metadata",
)
@cache()
async def get_image_location_endpoint(image_path: str) -> ImageGPSLocation:
    base_path = Path(config.DATA_PATH)
    full_file_path = (base_path / image_path).resolve()

    try:
        full_file_path.relative_to(base_path.resolve())
    except ValueError:
        raise HTTPException(
            status_code=403, detail="Access denied: Path outside allowed directory"
        )

    location = await get_image_location(image_path)
    return ImageGPSLocation(**location)
