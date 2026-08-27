"""
config.py - Environment & Provider Configuration for SynapseAir

Manages API keys, model endpoints, and communication webhooks for:
1. DeepSeek LLM (or Alibaba Cloud DashScope / OpenAI compatible)
2. Hermes LLM (or Ollama / local function calling)
3. n8n (WhatsApp / Telegram webhook gateway)
4. Atlas Sandbox API

Phase 4: Refactored to Pydantic BaseSettings with env profiles & validation.
"""

import os
import warnings
from typing import Literal, Optional

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine env file based on environment profile
_ENV = os.getenv("ENVIRONMENT", "development")
_ENV_FILE = {
    "development": ".env",
    "staging": ".env.staging",
    "production": ".env.production",
}.get(_ENV, ".env")


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env files."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────
    APP_NAME: str = "SynapseAir Travel Recovery OS"
    DEBUG: bool = True
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    SYNAPSE_API_SECRET: str = "default-insecure-secret-change-in-prod"
    REQUIRE_AUTH: bool = False

    # ── DeepSeek LLM (Main Reasoning & Arbiter) ─────────────────────────
    DEEPSEEK_API_KEY: Optional[str] = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # ── Hermes / Local LLM (Function Calling & Parsing) ──────────────────
    HERMES_API_BASE: str = "http://localhost:11434/v1"
    HERMES_API_KEY: str = "ollama"
    HERMES_MODEL: str = "hermes3:latest"

    # ── n8n Webhook & API (WhatsApp Gateway) ─────────────────────────────
    N8N_API_URL: str = "http://127.0.0.1:5678"
    N8N_API_KEY: Optional[str] = ""
    N8N_WEBHOOK_URL: Optional[str] = ""
    N8N_CONSENSUS_CALLBACK_URL: str = "http://127.0.0.1:8000/webhook/consensus"

    # ── Atlas Official GDS API (Sandbox & Production) ──────────────────
    ATLAS_ENV: Literal["sandbox", "production"] = "sandbox"
    ATLAS_CLIENT_ID: str = "CTR12752_api_1"
    ATLAS_CLIENT_SECRET: str = "sandbox-sk-CTR12752_api_1"
    ATLAS_BASE_URL: str = "https://sandbox.atriptech.com"
    ATLAS_SEARCH_BASE_URL: Optional[str] = None       # Populated in Prod from ATRIP Company Information
    ATLAS_TRANSACTION_BASE_URL: Optional[str] = None  # Populated in Prod from ATRIP Company Information
    ATLAS_API_KEY: Optional[str] = "CTR12752_api_1"

    # ── Redis ────────────────────────────────────────────────────────────
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"

    # ── JWT Auth ─────────────────────────────────────────────────────────
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # ── Observability ────────────────────────────────────────────────────
    OTEL_ENDPOINT: Optional[str] = ""
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False

    @field_validator("JWT_SECRET_KEY", mode="before")
    @classmethod
    def default_jwt_secret(cls, v: Optional[str], info) -> str:
        """Fall back to SYNAPSE_API_SECRET if JWT_SECRET_KEY is not set."""
        if not v:
            return info.data.get("SYNAPSE_API_SECRET", "default-insecure-secret-change-in-prod")
        return v

    @model_validator(mode="after")
    def validate_production(self) -> "Settings":
        """Warn (don't crash) if production is missing critical keys."""
        if self.ENVIRONMENT == "production":
            missing = []
            if self.SYNAPSE_API_SECRET == "default-insecure-secret-change-in-prod":
                missing.append("SYNAPSE_API_SECRET")
            if not self.DEEPSEEK_API_KEY:
                missing.append("DEEPSEEK_API_KEY")
            if self.JWT_SECRET_KEY in ("default-insecure-secret-change-in-prod", None):
                missing.append("JWT_SECRET_KEY")
            if not self.REDIS_URL:
                missing.append("REDIS_URL")
            if missing:
                warnings.warn(
                    f"Production mode with default/missing keys: {', '.join(missing)}. "
                    "Set these before going live.",
                    RuntimeWarning,
                    stacklevel=2,
                )
        return self


settings = Settings()
