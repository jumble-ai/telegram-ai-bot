from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from tg_agent.config import Settings
from tg_agent.handlers import echo_router
from tg_agent.services.calendar import GoogleCalendarClient
from tg_agent.services.crypto_pay import CryptoPayClient
from tg_agent.services.history import HistoryRepository
from tg_agent.services.openrouter import OpenRouterClient
from tg_agent.services.search import TavilySearchClient


def build_dispatcher(
    ai_client: OpenRouterClient,
    history_repository: HistoryRepository,
    search_client: TavilySearchClient | None,
    crypto_pay_client: CryptoPayClient | None,
    calendar_client: GoogleCalendarClient | None,
) -> Dispatcher:
    """Create dispatcher and register routers."""
    dispatcher = Dispatcher(
        ai_client=ai_client,
        history_repository=history_repository,
        search_client=search_client,
        crypto_pay_client=crypto_pay_client,
        calendar_client=calendar_client,
    )
    dispatcher.include_router(echo_router)
    return dispatcher


def build_bot(settings: Settings) -> Bot:
    """Create configured aiogram bot."""
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def build_ai_client(settings: Settings) -> OpenRouterClient:
    """Create configured OpenRouter client."""
    return OpenRouterClient(
        api_key=settings.openrouter_api_key,
        model=settings.openrouter_model,
        image_model=settings.openrouter_image_model,
        stt_model=settings.openrouter_stt_model,
        tts_model=settings.openrouter_tts_model,
        tts_voice=settings.openrouter_tts_voice,
    )


def build_history_repository(settings: Settings) -> HistoryRepository:
    """Create configured history repository."""
    return HistoryRepository(database_path=settings.database_path)


def build_search_client(settings: Settings) -> TavilySearchClient | None:
    """Create configured Tavily search client if API key is set."""
    if not settings.tavily_api_key:
        return None
    return TavilySearchClient(api_key=settings.tavily_api_key)


def build_crypto_pay_client(settings: Settings) -> CryptoPayClient | None:
    """Create configured Crypto Pay client if API token is set."""
    if not settings.crypto_pay_api_token:
        return None
    return CryptoPayClient(api_token=settings.crypto_pay_api_token)


def build_calendar_client(settings: Settings) -> GoogleCalendarClient | None:
    """Create configured Google Calendar client if credentials are set."""
    if not settings.google_service_account_client_email:
        return None
    if not settings.google_service_account_private_key:
        return None
    if not settings.google_calendar_id:
        return None
    return GoogleCalendarClient(
        service_account_info={
            "type": "service_account",
            "client_email": settings.google_service_account_client_email,
            "private_key": settings.google_service_account_private_key,
            "token_uri": settings.google_service_account_token_uri
            or "https://oauth2.googleapis.com/token",
        },
        calendar_id=settings.google_calendar_id,
        time_zone=settings.google_calendar_timezone,
    )
