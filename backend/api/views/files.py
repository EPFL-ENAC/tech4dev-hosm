"""
Handle local file operations
"""

import json
import logging
import re
import zipfile
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote
from uuid import uuid4

import httpx
from api.auth import get_admin_user
from api.config import config
from api.models.auth import User
from api.models.files import (
    Contribution,
    StonesResponse,
    UploadInfo,
    UploadInfoState,
    extract_stone_number,
)
from api.services.files import (
    delete_local_upload_folder,
    get_lfs_url,
    get_local_file_content,
    get_local_file_lfs_id,
    list_local_files,
    update_local_upload_info_state,
    upload_local_files,
)
from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException
from fastapi.datastructures import UploadFile
from fastapi.param_functions import File
from fastapi.responses import Response, StreamingResponse
from fastapi_cache.decorator import cache

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
        lfs_id = get_local_file_lfs_id(full_file_path)
        if lfs_id:
            url = get_lfs_url(lfs_id)

            async def stream_lfs_file():
                async with httpx.AsyncClient() as client:
                    async with client.stream("GET", url) as response:
                        if response.status_code != 200:
                            raise HTTPException(
                                status_code=500,
                                detail=f"Error fetching LFS file from remote server: {response.status_code}",
                            )
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            yield chunk

            headers = {
                "Content-Disposition": content_disposition(f"{Path(file_path).name}")
            }
            return StreamingResponse(
                stream_lfs_file(),
                media_type="application/octet-stream",
                headers=headers,
            )

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
