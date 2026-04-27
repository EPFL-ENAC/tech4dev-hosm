from functools import lru_cache

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    APP_URL: str = "http://localhost:9000"
    API_PATH: str = ""
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 30

    AZURE_MAPS_KEY: str = ""
    MAPBOX_ACCESS_TOKEN: str = ""

    CODES_ANNOTATORS: list[str]
    CODES_REVIEWERS: list[str]

    DB_HOST: str
    DB_PORT: int = 5432
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    @property
    def DB_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    IMAGE_EXTENSIONS: list[str] = [".jpg"]
    DATASETS: list[str] = [
        "datasets/raw-images/1_Sample_Data_Melamchi_Bazar_Area_Flooding",
        "datasets/raw-images/2_Sample_Data_Melamchi_Bazar_Access_Road_Section_Flooding",
        "datasets/raw-images/3_Sample_Data_KTM_Flooding",
        "datasets/raw-images/4_Sample_Data_Jajarkot_Rukum_West/4202-337ac79e-92fc-4126-87e2-2f31298524bf_raw_images",
        "datasets/raw-images/4_Sample_Data_Jajarkot_Rukum_West/4205-1809d422-0af9-4a60-a1d8-7a3017baab98_raw_images",
        "datasets/raw-images/4_Sample_Data_Jajarkot_Rukum_West/4209-d298c5a6-b7f8-4615-bcda-bf3b7d301810_raw_images",
        "datasets/raw-images/4_Sample_Data_Jajarkot_Rukum_West/4210-64fe11ff-2dc5-42d2-aad8-a67463b17c9b_raw_images",
    ]
    DATA_PATH: str = ""

    N_FEATURES: int = 5000
    N_MATCHES: int = 1000


@lru_cache()
def get_config():
    return Config()


config = get_config()
