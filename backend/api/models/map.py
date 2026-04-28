from pydantic import BaseModel


class TileSourceResponse(BaseModel):
    """Tile source configuration for a map provider."""

    tiles: list[str]
    tile_size: int
    attribution: str
    min_zoom: int
    max_zoom: int
