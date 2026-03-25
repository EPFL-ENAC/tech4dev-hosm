import mimetypes
import subprocess
from functools import cache
from logging import getLogger
from pathlib import Path

from api.config import config

logger = getLogger("uvicorn.error")


def _ensure_data_directory_mounted():
    """Check whether the data directory is mounted, and if not mount it using rclone mount."""
    data_path = Path(config.DATA_PATH)

    if data_path.exists() and any(data_path.iterdir()):
        return

    data_path.mkdir(parents=True, exist_ok=True)
    subprocess.Popen(
        [
            "rclone",
            "mount",
            f"{config.DATA_RCLONE_NAME}:{config.DATA_REMOTE_PATH}",
            str(data_path),
        ],
        start_new_session=True,
    )


@cache
def get_local_file_content(file_path: Path) -> tuple[bytes | None, str | None]:
    """Read file content and determine MIME type."""
    _ensure_data_directory_mounted()

    if not file_path.exists():
        return None, None

    with open(file_path, "rb") as f:
        content = f.read()

    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type is None:
        mime_type = "application/octet-stream"

    return content, mime_type


def list_local_files(directory_path: Path) -> list[str]:
    """List all files in a directory recursively."""
    _ensure_data_directory_mounted()

    logger.info(f"Listing files in directory: {directory_path}")
    if not directory_path.exists() or not directory_path.is_dir():
        return []

    files = []
    for item in directory_path.rglob("*"):
        if item.is_file():
            files.append(str(item))

    return files
