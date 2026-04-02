"""
Get image urls and files.
"""

import logging

from fastapi import APIRouter

from api.models.images import OverlapResponse
from api.services.images import (
    get_best_overlap,
    get_best_overlap_with_others,
    get_image_resolution,
)

logger = logging.getLogger("uvicorn.error")
router = APIRouter()


@router.post(
    "/next-overlap/{image_path:path}",
    status_code=200,
    description="Get the next image path that overlaps most with the given image",
)
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
