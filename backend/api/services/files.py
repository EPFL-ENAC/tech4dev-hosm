import asyncio
import io
import mimetypes
import subprocess
from functools import cache
from logging import getLogger
from pathlib import Path

import asyncssh
from PIL import Image

from api.config import config

logger = getLogger("uvicorn.error")

CHUNK_SIZE = 65536


@cache
def get_local_file_content(file_path: Path) -> tuple[bytes | None, str | None]:
    """Read file content and determine MIME type."""

    if not file_path.exists():
        return None, None

    with open(file_path, "rb") as f:
        content = f.read()

    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type is None:
        mime_type = "application/octet-stream"

    if mime_type == "image/jpeg":
        image = Image.open(io.BytesIO(content))
        if not image.info.get("progressive", False):
            output = io.BytesIO()
            image.save(
                output,
                format="JPEG",
                progressive=True,
                optimize=False,
                quality=70,
            )
            content = output.getvalue()

    return content, mime_type


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
