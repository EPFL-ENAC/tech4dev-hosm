"""
Get image urls and files.
"""

import logging

from fastapi import APIRouter

from api.models.images import NextOverlapResponse
from api.services.images import get_best_overlap

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
) -> NextOverlapResponse | None:
    overlap = await get_best_overlap(image_path, excluded_image_names)

    return (
        NextOverlapResponse(
            image_path=overlap[0],
            homography_matrix=overlap[1],
            overlap_ratio=overlap[2],
        )
        if overlap
        else None
    )
