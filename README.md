# tg-agent

🤖 Telegram-бот на aiogram 3.27+, который общается через OpenRouter, помнит
последние 10 сообщений в SQLite, рисует изображения, ищет информацию в сети,
создает события в Google Календаре, принимает донаты и голосовые сообщения.

## Возможности

- 💬 **AI-чат** с памятью последних 10 сообщений через OpenRouter
- 🎨 **Генерация изображений** по текстовому описанию
- 🔎 **Поиск в интернете** через Tavily с форматированием ответа AI
- 🎙️ **Распознавание голоса** (OGG/Opus → WAV через PyAV) и аудиофайлов `.mp3`/`.wav`
- 🔊 **Text-to-Speech** (озвучка текста)
- 🧾 **Создание счетов** через Crypto Pay (USDT, TON, BTC)
- 📅 **Создание событий** в Google Календаре из естественного языка
- 💝 **Донаты** через Crypto Pay

## Стек

- **Python 3.11+** с `uv` для управления зависимостями
- **aiogram 3.27+** — асинхронный фреймворк для Telegram
- **OpenRouter** — доступ к LLM (GPT, Claude, Gemini и др.)
- **Tavily** — поиск в интернете
- **Crypto Pay** — криптовалютные платежи
- **Google Calendar API** — управление календарем
- **SQLite** + **aiosqlite** — персистентная память диалогов

## Переменные окружения

Скопируйте `.env.example` в `.env` и заполните:

### Обязательные

| Переменная | Описание | Где получить |
|------------|----------|--------------|
| `BOT_TOKEN` | Токен Telegram-бота | [@BotFather](https://t.me/BotFather) |
| `OPENROUTER_API_KEY` | API-ключ OpenRouter | [openrouter.ai/keys](https://openrouter.ai/keys) |
| `TAVILY_API_KEY` | API-ключ Tavily | [app.tavily.com](https://app.tavily.com) |
| `CRYPTO_PAY_API_TOKEN` | Токен Crypto Pay | [@CryptoBot](https://t.me/CryptoBot) → Crypto Pay |
| `GOOGLE_SERVICE_ACCOUNT_CLIENT_EMAIL` | Email service account | [Google Cloud Console](https://console.cloud.google.com/) |
| `GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY` | Приватный ключ service account | Google Cloud Console |
| `GOOGLE_CALENDAR_ID` | ID календаря Google | Настройки календаря в Google |

### Опциональные

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `OPENROUTER_MODEL` | `openrouter/free` | Модель для текстового чата |
| `OPENROUTER_IMAGE_MODEL` | `google/gemini-3.1-flash-image-preview` | Модель для генерации изображений |
| `OPENROUTER_STT_MODEL` | `openai/gpt-4o-audio-preview` | Модель для распознавания речи |
| `OPENROUTER_TTS_MODEL` | `openai/gpt-4o-mini-tts-2025-12-15` | Модель для синтеза речи |
| `OPENROUTER_TTS_VOICE` | `nova` | Голос для TTS |
| `GOOGLE_SERVICE_ACCOUNT_TOKEN_URI` | `https://oauth2.googleapis.com/token` | OAuth token endpoint |
| `GOOGLE_CALENDAR_TIMEZONE` | `Europe/Moscow` | Часовой пояс для календаря |
| `DATABASE_PATH` | `data/bot.sqlite3` | Путь к SQLite-базе |

## Настройка Google Calendar

1. Создайте проект в [Google Cloud Console](https://console.cloud.google.com/)
2. Включите **Google Calendar API** в `APIs & Services → Library`
3. Создайте **Service Account**: `IAM & Admin → Service Accounts → Create`
4. Создайте **ключ** для service account: `Keys → Add Key → JSON`
5. Из скачанного JSON-файла извлеките:
   - `client_email` → `GOOGLE_SERVICE_ACCOUNT_CLIENT_EMAIL`
   - `private_key` → `GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY` (в одну строку с `\n`)
   - `token_uri` → `GOOGLE_SERVICE_ACCOUNT_TOKEN_URI`
6. В Google Calendar добавьте service account в доступ:
   - Откройте настройки календаря → `Share with specific people`
   - Добавьте email service account с правом `Make changes to events`
7. Скопируйте **Calendar ID** из раздела `Integrate calendar` в `GOOGLE_CALENDAR_ID`
   - Для основного календаря это ваш Google email
   - **Не используйте** `primary` — для service account это его отдельный календарь

## Локальный запуск

```bash
# Установка зависимостей
uv sync

# Запуск бота
uv run tg-agent
```

## Запуск через Docker Compose (VPS)

```bash
# На VPS с Ubuntu
docker compose up -d --build

# Логи
docker compose logs -f bot

# Перезапуск
docker compose restart bot
```

SQLite хранится в примонтированной папке `./data/`, поэтому история переживает
перезапуск контейнера.

## Использование

### 💬 Обычный чат
Просто отправьте текст. Бот ответит с учетом последних 10 сообщений.

### 🎨 Генерация изображения
```
/image кот в космосе в стиле ретрофутуризма
```

### 🔎 Поиск в интернете
```
/search последние новости aiogram 3.27
```

### 🎙️ Голосовые сообщения
Отправьте голосовое сообщение или аудиофайл `.mp3`/`.wav`.
Бот конвертирует, распознает и ответит текстом.

### 🔊 Озвучка текста
```
/tts Привет! Это голосовой ответ.
```

### 🧾 Создание счета (Crypto Pay)
Напишите обычным текстом:
```
Создай счет на 15$
```
Бот распознает намерение через ИИ, создаст USD-счет с оплатой в USDT, TON или
BTC и вернет ссылку с кнопками «Оплатить» и «Поделиться».

### 📅 Создание события (Google Calendar)
Напишите обычным текстом:
```
Добавь встречу завтра с 13:00 на полчаса
```
Бот распознает намерение, дату и время через ИИ, создаст событие в Google
Календаре и вернет кнопку «Посмотреть событие».

### 💝 Донаты
```
/donate10
/donate100
```

## Архитектура

```
src/tg_agent/
├── main.py           # Точка входа, запуск polling
├── bot.py            # Фабрики: Bot, Dispatcher, клиенты
├── config.py         # Загрузка настроек из .env
├── handlers/
│   ├── __init__.py
│   └── echo.py       # Все обработчики сообщений
└── services/
    ├── __init__.py
    ├── openrouter.py  # OpenRouter API (чат, изображения, STT, TTS, интенты)
    ├── crypto_pay.py  # Crypto Pay API (инвойсы)
    ├── calendar.py    # Google Calendar API (события)
    ├── search.py      # Tavily API (поиск)
    ├── history.py     # SQLite-хранилище диалогов
    └── audio.py       # Конвертация аудио (OGG → WAV)
```

## Лицензия

MIT
