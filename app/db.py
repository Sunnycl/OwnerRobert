import aiosqlite
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "app.db")


class Database:
    def __init__(self) -> None:
        os.makedirs(DATA_DIR, exist_ok=True)

    async def initialize(self) -> None:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                  id TEXT PRIMARY KEY,
                  created_at TEXT NOT NULL
                );
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  conversation_id TEXT NOT NULL,
                  role TEXT NOT NULL,
                  content TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                );
                """
            )
            await db.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
                  content,
                  role,
                  conversation_id,
                  created_at,
                  content='messages',
                  content_rowid='id'
                );
                """
            )
            await db.execute(
                """
                CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
                  INSERT INTO messages_fts(rowid, content, role, conversation_id, created_at)
                  VALUES (new.id, new.content, new.role, new.conversation_id, new.created_at);
                END;
                """
            )
            await db.execute(
                """
                CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
                  INSERT INTO messages_fts(messages_fts, rowid, content) VALUES('delete', old.id, old.content);
                END;
                """
            )
            await db.execute(
                """
                CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
                  INSERT INTO messages_fts(messages_fts, rowid, content) VALUES('delete', old.id, old.content);
                  INSERT INTO messages_fts(rowid, content, role, conversation_id, created_at)
                  VALUES (new.id, new.content, new.role, new.conversation_id, new.created_at);
                END;
                """
            )
            await db.commit()

    async def ensure_conversation(self, conversation_id: str | None) -> str:
        cid = conversation_id or str(uuid.uuid4())
        if conversation_id is None:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "INSERT OR IGNORE INTO conversations(id, created_at) VALUES (?, ?)",
                    (cid, datetime.utcnow().isoformat()),
                )
                await db.commit()
        return cid

    async def add_message(self, conversation_id: str, role: str, content: str) -> None:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO messages(conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (conversation_id, role, content, datetime.utcnow().isoformat()),
            )
            await db.commit()

    async def get_recent_messages(self, conversation_id: str, limit: int = 12) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id DESC LIMIT ?",
                (conversation_id, limit),
            ) as cursor:
                rows = await cursor.fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    async def search_messages(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            try:
                async with db.execute(
                    """
                    SELECT m.id, m.conversation_id, m.role, m.content, m.created_at
                    FROM messages_fts f
                    JOIN messages m ON m.id = f.rowid
                    WHERE messages_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (query, limit),
                ) as cursor:
                    rows = await cursor.fetchall()
            except Exception:
                async with db.execute(
                    """
                    SELECT id, conversation_id, role, content, created_at
                    FROM messages
                    WHERE content LIKE ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (f"%{query}%", limit),
                ) as cursor:
                    rows = await cursor.fetchall()
        return [dict(r) for r in rows]
