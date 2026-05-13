from __future__ import annotations

import asyncio
import logging
import sys

from dotenv import load_dotenv

from tg_agent.bot import (
    build_ai_client,
    build_bot,
    build_calendar_client,
    build_crypto_pay_client,
    build_dispatcher,
    build_history_repository,
    build_search_client,
)
from tg_agent.config import load_settings


async def main() -> None:
    """Start bot long polling."""
    load_dotenv()
    settings = load_settings()
    bot = build_bot(settings)
    ai_client = build_ai_client(settings)
    history_repository = build_history_repository(settings)
    search_client = build_search_client(settings)
    crypto_pay_client = build_crypto_pay_client(settings)
    calendar_client = build_calendar_client(settings)
    await history_repository.init()
    dispatcher = build_dispatcher(
        ai_client,
        history_repository,
        search_client,
        crypto_pay_client,
        calendar_client,
    )

    await dispatcher.start_polling(bot)


def run() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())


if __name__ == "__main__":
    run()
