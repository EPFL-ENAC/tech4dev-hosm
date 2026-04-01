import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    APP_URL: str = "http://localhost:9000"
    API_PATH: str = ""

    DATA_PATH: str

    N_FEATURES: int = 5000
    N_MATCHES: int = 1000


@lru_cache()
def get_config():
    return Config()


config = get_config()
