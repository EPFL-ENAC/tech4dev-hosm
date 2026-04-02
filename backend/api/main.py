import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from logging import INFO, basicConfig, warning

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from pydantic import BaseModel

from api.config import config
from api.views.files import router as files_router
from api.views.images import router as images_router

basicConfig(level=INFO)

CACHE_AGE_SECONDS = 2592000  # 30 days


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
    yield


app = FastAPI(root_path=config.API_PATH, lifespan=lifespan)

origins = [config.APP_URL] if config.APP_URL else []
if not config.APP_URL:
    warning(
        "config.APP_URL is not set. CORS will not allow any origins. "
        "Set config.APP_URL to enable cross-origin requests."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def cache_control_middleware(request: Request, call_next):
    response: Response = await call_next(request)
    if response.status_code == status.HTTP_200_OK:
        response.headers["Cache-Control"] = f"public, max-age={CACHE_AGE_SECONDS}"
        response.headers["Expires"] = time.strftime(
            "%a, %d %b %Y %H:%M:%S GMT",
            time.gmtime(time.time() + CACHE_AGE_SECONDS),
        )
    return response


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"


@app.get(
    "/healthz",
    tags=["Healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
async def get_health() -> HealthCheck:
    """Endpoint to perform an API healthcheck."""

    return HealthCheck(status="OK")


app.include_router(
    files_router,
    prefix="/files",
    tags=["Files"],
)


app.include_router(
    images_router,
    prefix="/images",
    tags=["Images"],
)
