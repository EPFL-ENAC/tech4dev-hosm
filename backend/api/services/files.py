import io
import mimetypes
import re
from functools import cache
from logging import getLogger
from pathlib import Path
from typing import Callable

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image

from api.config import config
from api.utils import add_cache_headers

logger = getLogger("uvicorn.error")

CHUNK_SIZE = 65536


def get_file(
    file_path: str,
    get_file_content_func: Callable,
) -> StreamingResponse:
    full_file_path = get_full_path(Path(file_path))

    try:
        body, content_type = get_file_content_func(full_file_path)

        if body is not None:
            headers = {
                "Content-Disposition": content_disposition(f"{Path(file_path).name}")
            }

            def generate():
                chunk_size = 8192
                for i in range(0, len(body), chunk_size):
                    yield body[i : i + chunk_size]

            response = StreamingResponse(
                generate(), media_type=content_type, headers=headers
            )
            add_cache_headers(response)
            return response
        else:
            raise HTTPException(status_code=404, detail="File not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


def get_full_path(path: Path) -> Path:
    """Get the full path of a file or directory within the allowed data directory.
    Raise HTTPException if the given path is outside the allowed data directory.
    """

    base_path = Path(config.DATA_PATH)
    full_path = (base_path / path).resolve()

    try:
        full_path.relative_to(base_path.resolve())
    except ValueError:
        raise HTTPException(
            status_code=403, detail="Access denied: Path outside allowed directory"
        )

    return full_path


def content_disposition(filename: str) -> str:
    """Generate a Content-Disposition header value that supports UTF-8 filenames."""
    safe_ascii = filename.encode("ascii", "ignore").decode()
    if not safe_ascii:
        safe_ascii = "download"

    # Sanitize ASCII fallback
    safe_ascii = re.sub(r"[^A-Za-z0-9._-]", "_", safe_ascii)

    return f'inline; filename="{safe_ascii}"'


def get_local_file_content(file_path: Path) -> tuple[bytes | None, str | None]:
    """Read file content and determine MIME type."""

    if not file_path.exists():
        return None, None

    with open(file_path, "rb") as f:
        content = f.read()

    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type is None:
        mime_type = "application/octet-stream"

    return content, mime_type


@cache
def get_thumbnail(file_path: Path) -> tuple[bytes | None, str | None]:
    content, mime_type = get_local_file_content(file_path)

    if content is None or mime_type is None:
        return None, None

    if not mime_type.startswith("image/"):
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    image = Image.open(io.BytesIO(content))
    # Crop to square from center, then resize (fill without stretching)
    width, height = image.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    image = image.crop((left, top, left + side, top + side))
    image = image.resize((50, 50), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    image.save(
        output,
        format="WEBP",
        quality=50,
    )
    content = output.getvalue()

    return content, "image/webp"


def list_local_files(directory_path: Path) -> list[str]:
    """List all files in a directory recursively."""

    logger.info(f"Listing files in directory: {directory_path}")
    if not directory_path.exists() or not directory_path.is_dir():
        return []

    files = []
    for item in directory_path.rglob("*"):
        if item.is_file():
            files.append(str(item))

    return files
