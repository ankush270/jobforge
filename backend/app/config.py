"""Application configuration using pydantic-settings."""

import logging
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration — env vars override .env file values."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── Database ──────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://jobforge:jobforge_dev_secret@localhost:5432/jobforge"
    database_url_sync: str = "postgresql://jobforge:jobforge_dev_secret@localhost:5432/jobforge"

    # ── Redis ─────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Auth ──────────────────────────────────────────────────
    secret_key: str = "dev-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours

    # ── CORS ──────────────────────────────────────────────────
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ── LLM Providers ─────────────────────────────────────────
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    deepseek_api_key: str = ""
    groq_api_key: str = ""
    nvidia_nim_api_key: str = ""
    cerebras_api_key: str = ""
    cloudflare_api_key: str = ""
    openrouter_api_key: str = ""
    aion_labs_api_key: str = ""
    cohere_api_key: str = ""
    default_llm_model: str = "groq/openai/gpt-oss-120b"

    # ── Scraping ──────────────────────────────────────────────
    jobspy_proxy: str = ""

    # ── App ───────────────────────────────────────────────────
    upload_dir: Path = Path("./uploads")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    def setup_logging(self) -> None:
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
            datefmt="%H:%M:%S",
        )


settings = Settings()
