from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

import aiosqlite

MessageRole = Literal["user", "assistant"]


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """Message stored in conversation history."""

    role: MessageRole
    content: str


@dataclass(frozen=True, slots=True)
class HistoryRepository:
    """SQLite-backed chat history storage."""

    database_path: Path

    async def init(self) -> None:
        """Create required database tables."""
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(self.database_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_messages_chat_id_id
                ON messages (chat_id, id)
                """
            )
            await db.commit()

    async def add_message(
        self,
        chat_id: int,
        role: MessageRole,
        content: str,
    ) -> None:
        """Save one chat message."""
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute(
                """
                INSERT INTO messages (chat_id, role, content)
                VALUES (?, ?, ?)
                """,
                (chat_id, role, content),
            )
            await db.commit()

    async def get_recent_messages(
        self,
        chat_id: int,
        limit: int = 10,
    ) -> list[ChatMessage]:
        """Return recent chat messages in chronological order."""
        async with aiosqlite.connect(self.database_path) as db:
            async with db.execute(
                """
                SELECT role, content
                FROM messages
                WHERE chat_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (chat_id, limit),
            ) as cursor:
                rows = list(await cursor.fetchall())

        messages: list[ChatMessage] = []
        for role, content in reversed(rows):
            if role not in ("user", "assistant"):
                continue

            messages.append(
                ChatMessage(role=cast(MessageRole, role), content=str(content))
            )

        return messages
