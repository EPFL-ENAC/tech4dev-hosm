"""
Handle local file operations
"""

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi_cache.decorator import cache

from api.models.annotations import User
from api.services.auth import get_current_user
from api.services.files import (
    get_file as _get_file,
)
from api.services.files import (
    get_full_path,
    get_local_file_content,
    list_local_files,
)
from api.services.files import (
    get_thumbnail as _get_thumbnail,
)

logger = logging.getLogger("uvicorn.error")
router = APIRouter()


@router.get(
    "/get/{file_path:path}",
    status_code=200,
    description="Download any assets from data directory",
)
# FastAPI in-memory cache does not support binary responses
async def get_file(
    file_path: str,
) -> StreamingResponse:
    return _get_file(file_path, get_local_file_content)


@router.get(
    "/thumbnail/{file_path:path}",
    status_code=200,
    description="Get thumbnail for an image file if it exists.",
)
# FastAPI in-memory cache does not support binary responses
async def get_thumbnail(
    file_path: str,
) -> StreamingResponse:
    return _get_file(file_path, _get_thumbnail)


@router.get(
    "/list/{directory_path:path}",
    status_code=200,
    description="List files in a given directory path in data directory",
)
@cache()
async def list_files(
    directory_path: str,
    current_user: User = Depends(get_current_user),
):
    try:
        full_directory_path = get_full_path(Path(directory_path))
        files = list_local_files(full_directory_path)
        files = [
            Path(path).relative_to(full_directory_path).as_posix() for path in files
        ]

        return {"files": files}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
