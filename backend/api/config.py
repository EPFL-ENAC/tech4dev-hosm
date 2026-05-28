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

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "hosm"
    DB_USER: str = "hosm_user"
    DB_PASSWORD: str = "hosm_password"

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
        "datasets/raw-images/Bagmati/DJI_202409291320_001_ChobharEndPlan1",
        "datasets/raw-images/Bagmati/DJI_202409291320_002_ChobharEndPlan2",
        "datasets/raw-images/Bagmati/DJI_202409291349_004_ChobharEndPlan2",
        "datasets/raw-images/Bagmati/DJI_202409291432_006_ChobharEndPlan3",
        "datasets/raw-images/Bagmati/DJI_202409291549_009_ChobharEndPlan4",
        "datasets/raw-images/Bagmati/DJI_202409291549_010_ChobharEndPlan4",
        "datasets/raw-images/Bagmati/DJI_202410011045_012_ChobharEndPlan4",
        "datasets/raw-images/Bagmati/DJI_202410011119_014_ChobharEndPlan4",
        "datasets/raw-images/Bagmati/DJI_202410011119_015_ChobharEndPlan5",
        "datasets/raw-images/Bagmati/DJI_202410011154_001_ChobharEndPlan5",
        "datasets/raw-images/Bagmati/DJI_202410011154_002_ChobharEndPlan6",
        "datasets/raw-images/Bagmati/DJI_202410011223_017_ChobharEndPlan6",
        "datasets/raw-images/Bagmati/DJI_202410011223_018_ChobharEndPlan7",
        "datasets/raw-images/Melamchi/2_Melamchi_Bazar_Area/1_Input/1_Images/1_Flight_1",
        "datasets/raw-images/Melamchi/2_Melamchi_Bazar_Area/1_Input/1_Images/2_Flight_2",
        "datasets/raw-images/Melamchi/2_Melamchi_Bazar_Area/1_Input/2_Extra",
        "datasets/raw-images/Melamchi/3_Melamchi_Indrawati_Stretch/1_Input/1_Images/1_Flight_1",
        "datasets/raw-images/Melamchi/3_Melamchi_Indrawati_Stretch/1_Input/1_Images/2_Flight_2",
        "datasets/raw-images/Melamchi/3_Melamchi_Indrawati_Stretch/1_Input/1_Images/3_Flight_3",
        "datasets/raw-images/Melamchi/3_Melamchi_Indrawati_Stretch/1_Input/2_Extra/1_Flight_1",
        "datasets/raw-images/Melamchi/3_Melamchi_Indrawati_Stretch/1_Input/2_Extra/2_Flight_2",
        "datasets/raw-images/Melamchi/4_Melamchi_to_Chanaute/1_Input/1_Images/1_Flight_1",
        "datasets/raw-images/Melamchi/4_Melamchi_to_Chanaute/1_Input/1_Images/2_Flight_2",
        "datasets/raw-images/Melamchi/4_Melamchi_to_Chanaute/1_Input/1_Images/3_Flight_3",
        "datasets/raw-images/Melamchi/4_Melamchi_to_Chanaute/1_Input/1_Images/4_Flight_4",
        "datasets/raw-images/Melamchi/4_Melamchi_to_Chanaute/1_Input/1_Images/5_Flight_5",
        "datasets/raw-images/Melamchi/4_Melamchi_to_Chanaute/1_Input/2_Extra",
        "datasets/raw-images/Melamchi/6_Melamchi_Road/1_Input/1_Images/1_Day_1/1_Melamchi_Flight_01",
        "datasets/raw-images/Melamchi/6_Melamchi_Road/1_Input/1_Images/1_Day_1/2_Melamchi_2_Flight_01",
        "datasets/raw-images/Melamchi/6_Melamchi_Road/1_Input/1_Images/1_Day_1/3_Melamchi_3_Flight_01",
        "datasets/raw-images/Melamchi/6_Melamchi_Road/1_Input/1_Images/2_Day_2/Melamchi_4_Flight_01",
        "datasets/raw-images/Melamchi/6_Melamchi_Road/1_Input/1_Images/2_Day_2/Melamchi_4_Flight_02",
        "datasets/raw-images/Melamchi/6_Melamchi_Road/1_Input/1_Images/2_Day_2/Melamchi_5_Flight_01",
        "datasets/raw-images/Melamchi/6_Melamchi_Road/1_Input/1_Images/2_Day_2/Melamchi_5_Flight_02",
        "datasets/raw-images/Melamchi/6_Melamchi_Road/1_Input/1_Images/2_Day_2/Melamchi_5_Flight_03",
        "datasets/raw-images/Melamchi/6_Melamchi_Road/1_Input/1_Images/2_Day_2/Melamchi_5_Flight_04",
        "datasets/raw-images/Nakkhu/DJI_202504021045_005_Nakkhu-p1",
        "datasets/raw-images/Nakkhu/DJI_202504021120_007_Nakkhu-p1",
        "datasets/raw-images/Nakkhu/DJI_202504021401_009_Nakkhu-p1",
        "datasets/raw-images/Nakkhu/DJI_202504021401_010_Nakkhu-p2",
        "datasets/raw-images/Nakkhu/DJI_202504021431_012_Nakkhu-p2",
        "datasets/raw-images/Nakkhu/DJI_202504021457_014_Nakkhu-p2",
        "datasets/raw-images/Nakkhu/DJI_202504021621_016_P3",
    ]
    DATA_PATH: str = ""

    N_FEATURES: int = 5000
    N_MATCHES: int = 1000


@lru_cache()
def get_config():
    return Config()


config = get_config()
