"""
Map tile source providers.
"""

from fastapi import APIRouter, HTTPException
from fastapi_cache.decorator import cache
from pydantic import BaseModel

from api.config import config

router = APIRouter(tags=["Map"])

# Azure Maps tileset for satellite/aerial imagery (raster PNG, zoom 1–19)
# See: https://learn.microsoft.com/en-us/rest/api/maps/render/get-map-tile
AZURE_TILESET_ID = "microsoft.imagery"
AZURE_API_VERSION = "2024-04-01"
AZURE_TILE_SIZE = 256
AZURE_MIN_ZOOM = 1
AZURE_MAX_ZOOM = 19


class TileSourceResponse(BaseModel):
    """Tile source configuration for a map provider."""

    tiles: list[str]
    tile_size: int
    attribution: str
    min_zoom: int
    max_zoom: int


@router.get(
    "/azure/tiles",
    response_model=TileSourceResponse,
    summary="Get Azure Maps tile metadata",
)
@cache(expire=3600)
async def get_azure_tiles():
    """
    Return Azure Maps tile configuration for satellite/aerial imagery.

    Azure Maps uses a fixed tile URL pattern — no remote metadata call
    is needed. The subscription key is embedded in the tile URL template
    so MapLibre can request tiles directly from the Azure Atlas CDN.

    See: https://learn.microsoft.com/en-us/rest/api/maps/render/get-map-tile
    """
    if not config.AZURE_MAPS_KEY:
        raise HTTPException(
            status_code=501,
            detail="AZURE_MAPS_KEY not configured in backend",
        )

    tile_url = (
        f"https://atlas.microsoft.com/map/tile"
        f"?api-version={AZURE_API_VERSION}"
        f"&tilesetId={AZURE_TILESET_ID}"
        f"&subscription-key={config.AZURE_MAPS_KEY}"
        f"&zoom={{z}}&x={{x}}&y={{y}}"
    )

    return TileSourceResponse(
        tiles=[tile_url],
        tile_size=AZURE_TILE_SIZE,
        attribution="© Microsoft Corporation",
        min_zoom=AZURE_MIN_ZOOM,
        max_zoom=AZURE_MAX_ZOOM,
    )


# MapBox satellite imagery (raster PNG, zoom 1–22)
# See: https://docs.mapbox.com/mapbox-styles/guides/satellite-streets/
MAPBOX_TILESET_ID = "mapbox.satellite"
MAPBOX_TILE_SIZE = 256
MAPBOX_MIN_ZOOM = 1
MAPBOX_MAX_ZOOM = 22


@router.get(
    "/mapbox/tiles",
    response_model=TileSourceResponse,
    summary="Get MapBox tile metadata",
)
@cache(expire=3600)
async def get_mapbox_tiles():
    """
    Return MapBox tile configuration for satellite imagery.

    MapBox uses a fixed tile URL pattern — no remote metadata call
    is needed. The access token is embedded in the tile URL template
    so MapLibre can request tiles directly from the MapBox CDN.

    See: https://docs.mapbox.com/mapbox-styles/guides/satellite-streets/
    """
    if not config.MAPBOX_ACCESS_TOKEN:
        raise HTTPException(
            status_code=501,
            detail="MAPBOX_ACCESS_TOKEN not configured in backend",
        )

    tile_url = (
        f"https://api.mapbox.com/v4/{MAPBOX_TILESET_ID}/{{z}}/{{x}}/{{y}}@2x.png"
        f"?access_token={config.MAPBOX_ACCESS_TOKEN}"
    )

    return TileSourceResponse(
        tiles=[tile_url],
        tile_size=MAPBOX_TILE_SIZE,
        attribution="© Mapbox © OpenStreetMap",
        min_zoom=MAPBOX_MIN_ZOOM,
        max_zoom=MAPBOX_MAX_ZOOM,
    )
