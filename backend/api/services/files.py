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


def is_remote_dataset_path(path: Path) -> bool:
    """Check if the given path is under the remote dataset mount directory."""
    dataset_path = Path(config.DATA_PATH) / config.DATASET_MOUNT_DIR
    return path == dataset_path or dataset_path in path.parents


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


async def get_remote_file_content(file_path: Path) -> tuple[bytes | None, str | None]:
    """Read remote file content via SSH and determine MIME type."""
    mount_path = Path(config.DATA_PATH) / config.DATASET_MOUNT_DIR
    relative_path = file_path.relative_to(mount_path)
    remote_file_path = f"{config.DATASET_REMOTE_PATH}/{relative_path}"

    try:
        async with asyncssh.connect(
            config.DATASET_HOST,
            username=config.SSH_USERNAME,
            client_keys=[config.SSH_KEY_PATH],
            known_hosts=None,
        ) as conn:
            async with conn.start_sftp_client() as sftp:
                try:
                    attrs = await sftp.stat(str(remote_file_path))
                except asyncssh.SFTPNoSuchFile:
                    return None, None

                content = b""
                async with sftp.open(str(remote_file_path), "rb") as f:
                    while True:
                        chunk = await f.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        content += chunk

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

    except (OSError, asyncssh.Error) as exc:
        logger.error(f"SSH connection failed: {exc}")
        raise exc


async def list_remote_files(directory_path: Path) -> list[str]:
    """List all entries (files and directories) in a remote directory via SSH."""
    mount_path = Path(config.DATA_PATH) / config.DATASET_MOUNT_DIR
    relative_path = directory_path.relative_to(mount_path)
    remote_dir_path = f"{config.DATASET_REMOTE_PATH}/{relative_path}"

    try:
        async with asyncssh.connect(
            config.DATASET_HOST,
            username=config.SSH_USERNAME,
            client_keys=[config.SSH_KEY_PATH],
            known_hosts=None,
        ) as conn:
            async with conn.start_sftp_client() as sftp:
                try:
                    return await sftp.listdir(str(remote_dir_path))
                except asyncssh.SFTPNoSuchFile:
                    return []

    except (OSError, asyncssh.Error) as exc:
        logger.error(f"SSH connection failed: {exc}")
        raise exc
