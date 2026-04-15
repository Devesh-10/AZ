"""Configuration for AZ Document Query backend."""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    embedding_model: str = "all-MiniLM-L6-v2"
    top_k_results: int = 5
    chunk_size: int = 500
    chunk_overlap: int = 50

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
