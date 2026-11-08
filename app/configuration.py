import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "shorts-cpep")
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    # MUST be the same database name shorts-nlp writes cpep_models into
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE")
    API_ACCESS_KEY: str = os.getenv("API_ACCESS_KEY", "")


settings = Settings()