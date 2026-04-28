"""
Map tile source providers.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi_cache.decorator import cache

from api.config import config
from api.models.annotations import User
from api.models.map import TileSourceResponse
from api.services.auth import get_current_user

router = APIRouter()


# Esri World Imagery (raster PNG, zoom 0–19)
# See: https://worldimagery.arcgis.com/home/
ESRI_TILE_SIZE = 256
ESRI_MIN_ZOOM = 0
ESRI_MAX_ZOOM = 19


@router.get(
    "/esri/tiles",
    description="Get Esri World Imagery tile metadata",
)
@cache(expire=3600)
async def get_esri_tiles(
    current_user: User = Depends(get_current_user),
) -> TileSourceResponse:
    """
    Return Esri World Imagery tile configuration.

    Esri World Imagery is a free, open tile service — no API key is
    required.  The tile URL follows the standard ArcGIS MapServer pattern
    so MapLibre can request tiles directly from the Esri CDN.

    See: https://worldimagery.arcgis.com/home/
    """
    tile_url = (
        "https://services.arcgisonline.com/ArcGIS/rest/services/"
        "World_Imagery/MapServer/tile/{z}/{y}/{x}"
    )

    return TileSourceResponse(
        tiles=[tile_url],
        tile_size=ESRI_TILE_SIZE,
        attribution="Source: Esri, Vantor, Earthstar Geographics, and the GIS User Community",
        min_zoom=ESRI_MIN_ZOOM,
        max_zoom=ESRI_MAX_ZOOM,
    )


# Azure Maps tileset for satellite/aerial imagery (raster PNG, zoom 1–19)
# See: https://learn.microsoft.com/en-us/rest/api/maps/render/get-map-tile
AZURE_TILESET_ID = "microsoft.imagery"
AZURE_API_VERSION = "2024-04-01"
AZURE_TILE_SIZE = 256
AZURE_MIN_ZOOM = 1
AZURE_MAX_ZOOM = 19


@router.get(
    "/azure/tiles",
    description="Get Azure Maps tile metadata",
)
@cache(expire=3600)
async def get_azure_tiles(
    current_user: User = Depends(get_current_user),
) -> TileSourceResponse:
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


# Mapbox satellite imagery (raster PNG, zoom 1–22)
# See: https://docs.mapbox.com/mapbox-styles/guides/satellite-streets/
MAPBOX_TILESET_ID = "mapbox.satellite"
MAPBOX_TILE_SIZE = 256
MAPBOX_MIN_ZOOM = 1
MAPBOX_MAX_ZOOM = 22


@router.get(
    "/mapbox/tiles",
    description="Get Mapbox tile metadata",
)
@cache(expire=3600)
async def get_mapbox_tiles(
    current_user: User = Depends(get_current_user),
) -> TileSourceResponse:
    """
    Return Mapbox tile configuration for satellite imagery.

    Mapbox uses a fixed tile URL pattern — no remote metadata call
    is needed. The access token is embedded in the tile URL template
    so MapLibre can request tiles directly from the Mapbox CDN.

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
