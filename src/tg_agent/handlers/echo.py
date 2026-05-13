from __future__ import annotations

import logging
from datetime import datetime
from io import BytesIO
from urllib.parse import quote
from zoneinfo import ZoneInfo

from aiogram import Bot, F, Router, html
from aiogram.enums import ChatAction
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import (
    BufferedInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from tg_agent.services.audio import AudioConversionError, convert_ogg_opus_to_wav
from tg_agent.services.calendar import (
    CalendarEvent,
    GoogleCalendarClient,
    GoogleCalendarError,
)
from tg_agent.services.crypto_pay import (
    CryptoPayClient,
    CryptoPayError,
    DonationInvoice,
    PaymentInvoice,
)
from tg_agent.services.history import HistoryRepository
from tg_agent.services.openrouter import (
    CalendarEventIntent,
    InvoiceIntent,
    OpenRouterClient,
    OpenRouterError,
)
from tg_agent.services.search import SearchError, TavilySearchClient

logger = logging.getLogger(__name__)
router = Router(name="echo")


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """Handle the /start command."""
    user_name = message.from_user.full_name if message.from_user else "друг"
    await message.answer(
        f"👋 Привет, {html.bold(html.quote(user_name))}!\n\n"
        "🤖 Напиши обычное сообщение — отвечу с учетом последних 10 реплик.\n"
        "🎨 Хочешь картинку? Используй: /image уютный робот в кафе\n"
        "🔎 Нужно найти инфу в сети? Используй: /search новости aiogram\n"
        "🎙️ Голосовое распознаю, .mp3/.wav тоже поддерживаю.\n"
        "🔊 Озвучить текст: /tts привет, как дела?\n"
        "💝 Поддержать проект: /donate10 или /donate100"
    )


@router.message(Command("image"))
async def image_handler(
    message: Message,
    command: CommandObject,
    bot: Bot,
    ai_client: OpenRouterClient,
) -> None:
    """Generate image by prompt from /image command."""
    prompt = command.args.strip() if command.args else ""
    if not prompt:
        await message.answer(
            "🎨 Добавь описание картинки после команды.\n\n"
            "Например: /image кот-космонавт на Марсе"
        )
        return

    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_PHOTO)

    try:
        image = await ai_client.generate_image(prompt)
    except OpenRouterError:
        await message.answer(
            "😕 Не получилось создать изображение.\n"
            "Попробуй чуть позже или измени описание."
        )
        return

    photo = BufferedInputFile(
        file=image.content,
        filename=f"generated.{image.extension}",
    )
    await message.answer_photo(photo=photo)


@router.message(Command("tts"))
async def tts_handler(
    message: Message,
    command: CommandObject,
    bot: Bot,
    ai_client: OpenRouterClient,
) -> None:
    """Synthesize speech by text from /tts command."""
    text = command.args.strip() if command.args else ""
    if not text:
        await message.answer(
            "🔊 Добавь текст после команды.\n\n"
            "Например: /tts Привет! Это голосовой ответ."
        )
        return

    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_VOICE)

    try:
        speech = await ai_client.synthesize_speech(text)
    except OpenRouterError:
        await message.answer(
            "😕 Не получилось озвучить текст.\nПопробуй еще раз чуть позже."
        )
        return

    audio = BufferedInputFile(
        file=speech.content,
        filename=f"speech.{speech.extension}",
    )
    await message.answer_audio(audio=audio, title="AI voice")


@router.message(Command("search"))
async def search_handler(
    message: Message,
    command: CommandObject,
    bot: Bot,
    ai_client: OpenRouterClient,
    search_client: TavilySearchClient,
) -> None:
    """Search the web by query from /search command."""
    query = command.args.strip() if command.args else ""
    if not query:
        await message.answer(
            "🔎 Добавь поисковый запрос после команды.\n\n"
            "Например: /search что нового в aiogram 3.27"
        )
        return

    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    try:
        search_response = await search_client.search(query)
        answer = await ai_client.format_search_answer(query, search_response)
    except SearchError:
        await message.answer(
            "🫠 Не получилось найти информацию.\n"
            "Попробуй другой запрос или повтори позже."
        )
        return
    except OpenRouterError:
        await message.answer(
            "🔎 Данные нашел, но не смог красиво оформить ответ через ИИ.\n"
            "Попробуй повторить запрос позже."
        )
        return

    await message.answer(answer)


@router.message(Command("donate10"))
async def donate_10_handler(
    message: Message,
    crypto_pay_client: CryptoPayClient,
) -> None:
    """Create a 10 USD donation invoice."""
    await _send_donation_invoice(message, crypto_pay_client, amount_usd=10)


@router.message(Command("donate100"))
async def donate_100_handler(
    message: Message,
    crypto_pay_client: CryptoPayClient,
) -> None:
    """Create a 100 USD donation invoice."""
    await _send_donation_invoice(message, crypto_pay_client, amount_usd=100)


@router.message(F.voice)
async def voice_handler(
    message: Message,
    bot: Bot,
    ai_client: OpenRouterClient,
    history_repository: HistoryRepository,
) -> None:
    """Convert Telegram voice message to WAV, transcribe and answer with AI."""
    if not message.voice:
        return

    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    buffer = BytesIO()
    await bot.download(message.voice.file_id, destination=buffer)

    try:
        converted_audio = convert_ogg_opus_to_wav(buffer.getvalue())
    except AudioConversionError as error:
        logger.warning("Failed to convert voice message: %s", error)
        await message.answer(
            "😕 Не получилось подготовить голосовое к распознаванию.\n"
            "Попробуй записать еще раз или пришли .mp3/.wav файл."
        )
        return

    await _transcribe_and_answer(
        message=message,
        ai_client=ai_client,
        history_repository=history_repository,
        audio=converted_audio.content,
        audio_format=converted_audio.format,
    )


@router.message(F.audio | F.document)
async def audio_stt_handler(
    message: Message,
    bot: Bot,
    ai_client: OpenRouterClient,
    history_repository: HistoryRepository,
) -> None:
    """Transcribe MP3/WAV audio file and answer with AI."""
    file_id, audio_format = _get_supported_audio_file(message)
    if not file_id or not audio_format:
        await message.answer(
            "🎙️ Для распознавания пришли аудиофайл в формате .mp3 или .wav."
        )
        return

    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    buffer = BytesIO()
    await bot.download(file_id, destination=buffer)

    await _transcribe_and_answer(
        message=message,
        ai_client=ai_client,
        history_repository=history_repository,
        audio=buffer.getvalue(),
        audio_format=audio_format,
    )


async def _transcribe_and_answer(
    message: Message,
    ai_client: OpenRouterClient,
    history_repository: HistoryRepository,
    audio: bytes,
    audio_format: str,
) -> None:
    """Transcribe audio, save it to history and answer with AI."""

    try:
        transcript = await ai_client.transcribe_audio(audio, audio_format=audio_format)
    except OpenRouterError as error:
        logger.warning("Failed to transcribe voice message: %s", error)
        await message.answer(
            "😕 Не получилось распознать голосовое.\n"
            "Попробуй записать чуть короче или отправить текстом."
        )
        return

    await history_repository.add_message(
        chat_id=message.chat.id,
        role="user",
        content=transcript,
    )
    history = await history_repository.get_recent_messages(message.chat.id, limit=10)

    try:
        answer = await ai_client.answer(history)
    except OpenRouterError:
        await message.answer(
            "🎙️ Голос распознал, но не смог получить ответ от ИИ.\n"
            f"Текст: {html.quote(transcript)}"
        )
        return

    await history_repository.add_message(
        chat_id=message.chat.id,
        role="assistant",
        content=answer,
    )
    await message.answer(
        f"🎙️ Распознал:\n{html.quote(transcript)}\n\n🤖 Ответ:\n{answer}"
    )


def _get_supported_audio_file(message: Message) -> tuple[str | None, str | None]:
    if message.audio:
        return _detect_audio_format(
            file_id=message.audio.file_id,
            file_name=message.audio.file_name,
            mime_type=message.audio.mime_type,
        )

    if message.document:
        return _detect_audio_format(
            file_id=message.document.file_id,
            file_name=message.document.file_name,
            mime_type=message.document.mime_type,
        )

    return None, None


def _detect_audio_format(
    file_id: str,
    file_name: str | None,
    mime_type: str | None,
) -> tuple[str | None, str | None]:
    normalized_name = file_name.lower() if file_name else ""
    normalized_mime = mime_type.lower() if mime_type else ""

    if normalized_name.endswith(".mp3") or normalized_mime in {
        "audio/mp3",
        "audio/mpeg",
    }:
        return file_id, "mp3"

    if normalized_name.endswith(".wav") or normalized_mime in {
        "audio/wav",
        "audio/wave",
        "audio/x-wav",
    }:
        return file_id, "wav"

    return None, None


@router.message()
async def ai_answer_handler(
    message: Message,
    bot: Bot,
    ai_client: OpenRouterClient,
    history_repository: HistoryRepository,
    crypto_pay_client: CryptoPayClient,
    calendar_client: GoogleCalendarClient,
) -> None:
    """Answer text messages with an OpenRouter model."""
    if not message.text:
        await message.answer(
            "💬 Пока я лучше всего понимаю текст.\n"
            "Пришли сообщение словами — и я отвечу."
        )
        return

    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    try:
        invoice_intent = await ai_client.detect_invoice_intent(message.text)
    except OpenRouterError as error:
        logger.warning("Failed to detect invoice intent: %s", error)
        invoice_intent = None

    if invoice_intent:
        await _send_ai_invoice(message, crypto_pay_client, invoice_intent)
        return

    try:
        calendar_intent = await ai_client.detect_calendar_event_intent(
            text=message.text,
            now=datetime.now(ZoneInfo(calendar_client.time_zone)),
            time_zone=calendar_client.time_zone,
        )
    except OpenRouterError as error:
        logger.warning("Failed to detect calendar event intent: %s", error)
        calendar_intent = None

    if calendar_intent:
        await _send_calendar_event(message, calendar_client, calendar_intent)
        return

    await history_repository.add_message(
        chat_id=message.chat.id,
        role="user",
        content=message.text,
    )
    history = await history_repository.get_recent_messages(message.chat.id, limit=10)

    try:
        answer = await ai_client.answer(history)
    except OpenRouterError:
        await message.answer(
            "😕 Не получилось получить ответ от ИИ.\nПопробуй еще раз через минуту."
        )
        return

    await history_repository.add_message(
        chat_id=message.chat.id,
        role="assistant",
        content=answer,
    )
    await message.answer(answer)


async def _send_ai_invoice(
    message: Message,
    crypto_pay_client: CryptoPayClient,
    invoice_intent: InvoiceIntent,
) -> None:
    user_id = message.from_user.id if message.from_user else 0

    try:
        invoice = await crypto_pay_client.create_usd_invoice(
            amount_usd=invoice_intent.amount_usd,
            accepted_assets=invoice_intent.accepted_assets,
            description=invoice_intent.description,
            user_id=user_id,
        )
    except CryptoPayError:
        await message.answer(
            "😕 Не получилось создать счет через Crypto Pay.\n"
            "Попробуй еще раз чуть позже."
        )
        return

    await message.answer(
        _format_payment_invoice(invoice),
        reply_markup=_build_payment_invoice_keyboard(invoice),
    )


async def _send_calendar_event(
    message: Message,
    calendar_client: GoogleCalendarClient,
    calendar_intent: CalendarEventIntent,
) -> None:
    try:
        event = await calendar_client.create_event(
            summary=calendar_intent.summary,
            start_at=calendar_intent.start_at,
            end_at=calendar_intent.end_at,
            description=calendar_intent.description,
        )
    except GoogleCalendarError as error:
        logger.warning("Failed to create Google Calendar event: %s", error)
        await message.answer(
            "😕 Не получилось создать событие в Google Календаре.\n"
            "Проверь доступ к календарю и попробуй еще раз."
        )
        return

    await message.answer(
        _format_calendar_event(event),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Посмотреть событие",
                        url=event.html_link,
                    )
                ]
            ]
        ),
    )


async def _send_donation_invoice(
    message: Message,
    crypto_pay_client: CryptoPayClient,
    amount_usd: int,
) -> None:
    user_id = message.from_user.id if message.from_user else 0

    try:
        invoice = await crypto_pay_client.create_donation_invoice(
            amount_usd=amount_usd,
            user_id=user_id,
        )
    except CryptoPayError:
        await message.answer(
            "😕 Не получилось создать счет для доната.\nПопробуй еще раз чуть позже."
        )
        return

    await message.answer(
        _format_donation_invoice(invoice),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"💳 Оплатить ${amount_usd}",
                        url=invoice.payment_url,
                    )
                ]
            ]
        ),
    )


def _format_donation_invoice(invoice: DonationInvoice) -> str:
    return (
        "💝 Спасибо за желание поддержать проект!\n\n"
        f"💵 Сумма: ${invoice.amount}\n"
        f"🧾 Счет: #{invoice.invoice_id}\n\n"
        "Нажми кнопку ниже, чтобы оплатить через Crypto Pay."
    )


def _format_payment_invoice(invoice: PaymentInvoice) -> str:
    assets = ", ".join(invoice.accepted_assets)
    return (
        "🧾 Счет создан через Crypto Pay\n\n"
        f"💵 Сумма: {invoice.amount} {invoice.fiat}\n"
        f"🪙 Оплата: {assets}\n"
        f"🔗 Ссылка: {invoice.payment_url}\n\n"
        "Отправь ссылку клиенту или нажми «Поделиться»."
    )


def _build_payment_invoice_keyboard(invoice: PaymentInvoice) -> InlineKeyboardMarkup:
    share_text = f"Счет на {invoice.amount} {invoice.fiat}:"
    share_url = (
        "https://t.me/share/url?"
        f"url={quote(invoice.payment_url, safe='')}"
        f"&text={quote(share_text, safe='')}"
    )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💳 Оплатить", url=invoice.payment_url),
                InlineKeyboardButton(text="Поделиться", url=share_url),
            ]
        ]
    )


def _format_calendar_event(event: CalendarEvent) -> str:
    start_at = event.start_at.strftime("%d.%m.%Y %H:%M")
    end_at = event.end_at.strftime("%H:%M")
    return (
        "📅 Событие создано в Google Календаре\n\n"
        f"📝 Название: {html.quote(event.summary)}\n"
        f"🕒 Время: {start_at}–{end_at}\n"
        f"🌍 Часовой пояс: {html.quote(event.time_zone)}"
    )
