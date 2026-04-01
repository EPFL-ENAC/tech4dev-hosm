from pydantic import BaseModel


class NextOverlapResponse(BaseModel):
    """Response model for the next overlap endpoint."""

    image_path: str
    homography_matrix: list[list[float]]
    overlap_ratio: float
