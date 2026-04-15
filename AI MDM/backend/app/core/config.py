"""Configuration for MDM Agent backend."""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    aws_region: str = "us-east-1"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None

    # Bedrock model
    mdm_model: str = "us.anthropic.claude-sonnet-4-20250514-v1:0"

    # Reltio (mock or real - same shape)
    reltio_base_url: str = "http://127.0.0.1:8765"
    reltio_auth_token: str | None = None  # Bearer token for real Reltio

    host: str = "0.0.0.0"
    port: int = 3010

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
