import time

from fastapi import Response

CACHE_AGE_SECONDS = 604800  # 7 days


def add_cache_headers(response: Response) -> Response:
    if response.status_code == 200:
        response.headers["Cache-Control"] = f"public, max-age={CACHE_AGE_SECONDS}"
        response.headers["Expires"] = time.strftime(
            "%a, %d %b %Y %H:%M:%S GMT",
            time.gmtime(time.time() + CACHE_AGE_SECONDS),
        )
    return response
