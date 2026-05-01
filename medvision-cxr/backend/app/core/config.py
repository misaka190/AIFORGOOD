from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MedVision-CXR Backend"
    api_v1_prefix: str = "/api/v1"
    environment: str = "development"
    secret_key: str = Field(default="change-this-in-production", min_length=16)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/medvision_cxr"
    redis_url: str = "redis://localhost:6379/0"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket_raw: str = "cxr-raw"
    minio_bucket_outputs: str = "cxr-outputs"

    model_artifact_path: str = "artifacts/cxr_model.pt"
    model_version_name: str = "cxr-densenet121-v1.3.0"
    max_upload_mb: int = 15
    allow_dicom: bool = True
    cors_origins: list[str] = ["*"]

    local_storage_root: Path = Path("storage")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
