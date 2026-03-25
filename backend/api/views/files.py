"""
Handle local file operations
"""

import logging
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from fastapi_cache.decorator import cache

from api.config import config
from api.services.files import (
    get_local_file_content,
    list_local_files,
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
):
    base_path = Path(config.DATA_PATH)
    full_file_path = (base_path / file_path).resolve()

    try:
        full_file_path.relative_to(base_path.resolve())
    except ValueError:
        raise HTTPException(
            status_code=403, detail="Access denied: Path outside allowed directory"
        )

    try:
        body, content_type = get_local_file_content(full_file_path)
        if body is not None:
            headers = {
                "Content-Disposition": content_disposition(f"{Path(file_path).name}")
            }
            return Response(content=body, media_type=content_type, headers=headers)
        else:
            raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@router.get(
    "/list/{directory_path:path}",
    status_code=200,
    description="List files in a given directory path in data directory",
)
@cache()
async def list_files(
    directory_path: str,
):
    try:
        base_path = Path(config.DATA_PATH)
        full_directory_path = (base_path / directory_path).resolve()

        try:
            full_directory_path.relative_to(base_path.resolve())
        except ValueError:
            raise HTTPException(
                status_code=403, detail="Access denied: Path outside allowed directory"
            )

        files = list_local_files(full_directory_path)

        files = [
            Path(path).relative_to(full_directory_path).as_posix() for path in files
        ]

        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def content_disposition(filename: str) -> str:
    """Generate a Content-Disposition header value that supports UTF-8 filenames."""
    safe_ascii = filename.encode("ascii", "ignore").decode()
    if not safe_ascii:
        safe_ascii = "download"

    # Sanitize ASCII fallback
    safe_ascii = re.sub(r"[^A-Za-z0-9._-]", "_", safe_ascii)

    return f'attachment; filename="{safe_ascii}"'
