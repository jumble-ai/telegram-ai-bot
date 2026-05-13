from __future__ import annotations

from dataclasses import dataclass
from os import getenv
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    """Application settings loaded from environment."""

    bot_token: str
    openrouter_api_key: str
    openrouter_model: str
    openrouter_image_model: str
    openrouter_stt_model: str
    openrouter_tts_model: str
    openrouter_tts_voice: str
    tavily_api_key: str
    crypto_pay_api_token: str
    google_service_account_client_email: str
    google_service_account_private_key: str
    google_service_account_token_uri: str
    google_calendar_id: str
    google_calendar_timezone: str
    database_path: Path


def load_settings() -> Settings:
    """Load and validate application settings."""
    bot_token = getenv("BOT_TOKEN")
    if not bot_token:
        msg = "BOT_TOKEN is required. Put it into .env or environment variables."
        raise RuntimeError(msg)

    openrouter_api_key = getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        msg = "OPENROUTER_API_KEY is required. Put it into .env."
        raise RuntimeError(msg)

    tavily_api_key = getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        msg = "TAVILY_API_KEY is required. Put it into .env."
        raise RuntimeError(msg)

    crypto_pay_api_token = getenv("CRYPTO_PAY_API_TOKEN")
    if not crypto_pay_api_token:
        msg = "CRYPTO_PAY_API_TOKEN is required. Put it into .env."
        raise RuntimeError(msg)

    google_service_account_client_email = getenv("GOOGLE_SERVICE_ACCOUNT_CLIENT_EMAIL")
    if not google_service_account_client_email:
        msg = "GOOGLE_SERVICE_ACCOUNT_CLIENT_EMAIL is required. Put it into .env."
        raise RuntimeError(msg)

    google_service_account_private_key = getenv("GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY")
    if not google_service_account_private_key:
        msg = "GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY is required. Put it into .env."
        raise RuntimeError(msg)

    return Settings(
        bot_token=bot_token,
        openrouter_api_key=openrouter_api_key,
        openrouter_model=getenv("OPENROUTER_MODEL", "openrouter/free"),
        openrouter_image_model=getenv(
            "OPENROUTER_IMAGE_MODEL",
            "google/gemini-3.1-flash-image-preview",
        ),
        openrouter_stt_model=getenv(
            "OPENROUTER_STT_MODEL",
            "openai/gpt-4o-audio-preview",
        ),
        openrouter_tts_model=getenv(
            "OPENROUTER_TTS_MODEL",
            "openai/gpt-4o-mini-tts-2025-12-15",
        ),
        openrouter_tts_voice=getenv("OPENROUTER_TTS_VOICE", "nova"),
        tavily_api_key=tavily_api_key,
        crypto_pay_api_token=crypto_pay_api_token,
        google_service_account_client_email=google_service_account_client_email,
        google_service_account_private_key=google_service_account_private_key,
        google_service_account_token_uri=getenv(
            "GOOGLE_SERVICE_ACCOUNT_TOKEN_URI",
            "https://oauth2.googleapis.com/token",
        ),
        google_calendar_id=getenv("GOOGLE_CALENDAR_ID", "primary"),
        google_calendar_timezone=getenv("GOOGLE_CALENDAR_TIMEZONE", "Europe/Moscow"),
        database_path=Path(getenv("DATABASE_PATH", "data/bot.sqlite3")),
    )
