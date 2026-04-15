"""Configuration settings for TIA LangGraph Backend"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None

    # Model Configuration - one per agent role
    orchestrator_model: str = "us.anthropic.claude-sonnet-4-20250514-v1:0"
    requirement_model: str = "us.anthropic.claude-sonnet-4-20250514-v1:0"
    test_gen_model: str = "us.anthropic.claude-sonnet-4-20250514-v1:0"
    synthetic_data_model: str = "us.anthropic.claude-sonnet-4-20250514-v1:0"
    execution_model: str = "us.anthropic.claude-sonnet-4-20250514-v1:0"
    analysis_model: str = "us.anthropic.claude-sonnet-4-20250514-v1:0"
    refactor_model: str = "us.anthropic.claude-sonnet-4-20250514-v1:0"
    reporting_model: str = "us.anthropic.claude-sonnet-4-20250514-v1:0"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 3001
    debug: bool = True

    # Data paths
    data_dir: str = "data"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
