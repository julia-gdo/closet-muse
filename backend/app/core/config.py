from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    frontend_url: str = "http://localhost:3000"
    environment: str = "development"

    removebg_api_key: str
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_account_id: str
    r2_bucket_name: str
    gemini_api_key: str


@lru_cache
def get_settings() -> Settings:
    return Settings()
