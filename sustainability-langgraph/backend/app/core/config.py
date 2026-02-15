"""
Configuration settings for Sustainability Insight Agent
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # AWS Settings
    aws_region: str = os.getenv("AWS_REGION_NAME", "us-east-1")

    # Model Settings
    supervisor_model: str = os.getenv("SUPERVISOR_MODEL", "us.anthropic.claude-3-5-sonnet-20241022-v2:0")
    kpi_model: str = os.getenv("KPI_MODEL", "us.anthropic.claude-3-5-sonnet-20241022-v2:0")
    analyst_model: str = os.getenv("ANALYST_MODEL", "us.anthropic.claude-sonnet-4-20250514-v1:0")
    validator_model: str = os.getenv("VALIDATOR_MODEL", "us.anthropic.claude-3-5-haiku-20241022-v1:0")

    # App Settings
    app_name: str = "Sustainability Insight Agent"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
