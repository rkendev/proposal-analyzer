"""
Application configuration via pydantic-settings.

Values are loaded from environment variables.
In production: set in Railway dashboard.
In local dev: set in .env file (never committed to git).
"""

from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict


class Settings(BaseSettings):
    # LLM model names (via LiteLLM)
    cheap_model_name: str = Field(
        default="anthropic/claude-haiku-4-5-20251001",
        description="Model for extraction tasks (Job Intelligence, Rate Intelligence)"
    )
    strong_model_name: str = Field(
        default="anthropic/claude-sonnet-4-5-20250929",
        description="Model for reasoning tasks (Proposal Analyst, Win Strategy)"
    )

    # API key
    anthropic_api_key: str = Field(
        description="Anthropic API key from console.anthropic.com"
    )

    # CORS — set to Lovable app URL in production
    allowed_origin: str = Field(
        default="http://localhost:3000",
        description="CORS allowed origin. Set to Lovable URL in Railway."
    )

    # API config
    port: int = Field(default=8001)
    api_version: str = Field(default="1.0.0")

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
