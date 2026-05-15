from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        default="postgresql+asyncpg://opendpp:opendpp@localhost:5432/opendpp",
        description="Async SQLAlchemy DSN. Override via DATABASE_URL.",
    )
    app_name: str = "OpenDPP"
    debug: bool = False
    schema_path: Path = Field(
        default=Path(__file__).resolve().parents[3] / "schemas" / "textile-dpp.v1.json",
        description="Filesystem path to the textile DPP JSON Schema.",
    )
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:3030",
            "http://127.0.0.1:3030",
            "http://localhost:3000",
        ],
        description="Origins allowed by CORS — defaults to the Next.js dev server.",
    )

    # --- LLM layer --------------------------------------------------------
    llm_provider: str = Field(
        default="anthropic",
        description="Which ChatProvider to use: 'anthropic' or 'mock'. Falls back to 'mock' if anthropic is selected but no API key is set.",
    )
    anthropic_api_key: str | None = Field(
        default=None,
        description="Anthropic API key. Set via ANTHROPIC_API_KEY env var; never committed.",
    )
    anthropic_model: str = Field(
        default="claude-sonnet-4-6",
        description="Default Anthropic model id.",
    )
    llm_max_output_tokens: int = Field(default=1024)


@lru_cache
def get_settings() -> Settings:
    return Settings()
