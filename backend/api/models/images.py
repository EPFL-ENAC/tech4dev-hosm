from pydantic import BaseModel


class OverlapResponse(BaseModel):
    """Response model for the next overlap endpoint."""

    image_path: str
    homography_matrix: list[list[float]]
    overlap_ratio: float
    resolution: tuple[int, int]


class ImageGPSLocation(BaseModel):
    """Model for image location data."""

    latitude: float
    longitude: float
