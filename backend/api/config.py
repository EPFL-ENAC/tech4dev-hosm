import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    PATH_PREFIX: str = ""
    APP_URL: str = "http://localhost:9000"

    DATA_PATH: str
    DATASET_HOST: str
    DATASET_REMOTE_PATH: str
    DATASET_MOUNT_DIR: str = "datasets"  # Mounted inside DATA_PATH
    SSH_USERNAME: str
    SSH_KEY_PATH: str = os.path.expanduser("~/.ssh/id_ed25519")


@lru_cache()
def get_config():
    return Config()


config = get_config()
