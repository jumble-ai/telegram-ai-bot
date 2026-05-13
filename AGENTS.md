# AGENTS.md — Python правила (production + aiogram 3.27 + Karpathy Guidelines)

  

Ты — Senior Python Engineer. Пиши чистый, понятный и поддерживаемый код.

  

## Принципы (Karpathy Guidelines)

- **Простота превыше всего** — маленькое улучшение, которое добавляет сложность, не стоит того.

- Сначала думай → потом кодь (Think Before Coding).

- Явно проговаривай предположения и trade-offs.

- Делай **хирургические изменения** (surgical changes) — минимум диффа.

- Код должен быть настолько простым, чтобы через 6 месяцев ты сам его понимал без боли.

- Читаемость и простота > «умный» код

- Сначала рабочий код → потом рефакторинг и улучшения

  

## Поиск информации

- Когда тебя просят изучить доки или документацию, используй `context7` mcp.

  

## Стек (2026)

- Управление пакетами и окружением: **uv**

- Линтинг + формат: **Ruff**

- Типизация: **mypy** (без фанатизма)

- Тесты: **pytest**

- Docstrings: Google style

- Telegram-боты: **aiogram 3.27+**

  

## Код-стиль

- Python 3.11+

- `from __future__ import annotations`

- Type hints на публичных функциях и классах (внутренние — по ситуации)

- snake_case / PascalCase

- f-strings

- `pathlib.Path` вместо строк с путями

- ≤ 88 символов в строке

- 4 пробела

  

## Хорошие практики

- Маленькие функции с одной ответственностью

- Early return

- Context managers (`with`)

- `logger` вместо `print()`

- Явная обработка ошибок + осмысленные исключения

- Секреты только через `.env` + `python-dotenv`

- `dataclasses` для простых моделей, **Pydantic** для валидации/API

  

## aiogram 3.x (обязательные правила)

- **Всё асинхронно** (`async def` + `await`)

- Используй **Router** для модульности (не лепи всё в один файл)

- Регистрируй handlers через `@router.message()`, `@router.callback_query()` и т.д.

- Handlers должны быть тонкими: только валидация + вызов service слоя

- Используй **Magic Filters** (`F.text`, `F.photo`, `Command()` и др.)

- Для состояний — **FSM** (`aiogram.fsm`)

- FSM — только для пользовательских сценариев, не для бизнес-логики

- Middlewares: `BaseMiddleware` или async callable (outer/inner)

- Bot создавай с `DefaultBotProperties(parse_mode=ParseMode.HTML)`

- `asyncio.run(main())` + `dp.start_polling(bot)`

- Никогда не используй глобальные `Bot.get_current()` (передавай `bot: Bot` явно)

  

## Запрещено

- `import *`

- `except:` без типа

- Silent except

- `print()` в production

- Mutable default arguments

- Хардкод секретов и путей

- Синхронный код в handlers (кроме редких случаев)

  

## Архитектура

- Разделяй: `core/` (бизнес), `services/`, `infrastructure/`, `handlers/`, `routers/`, `keyboards/`

- Бизнес-логика не зависит от Telegram

  

## Тесты

- `pytest` + AAA

- Тестируем бизнес-логику

- Мокаем внешние сервисы

  

## Workflow с GPT/Claude

1. Сгенерируй простую рабочую версию

2. Упрости и почисти (Karpathy style)

3. Добавь типы, docstrings, логирование

4. Напиши тесты

5. Прогони:

```bash

uv run ruff check .

uv run ruff format .

uv run mypy .

uv run pytest