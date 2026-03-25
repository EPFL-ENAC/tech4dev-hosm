import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    PATH_PREFIX: str = ""
    APP_URL: str = "http://localhost:9000"

    DATA_PATH: str
    DATA_RCLONE_NAME: str
    DATA_HOST: str
    DATA_REMOTE_PATH: str


@lru_cache()
def get_config():
    return Config()


config = get_config()
