from __future__ import annotations
import aiosqlite
import os
from typing import Optional
from db.schema import ALL_TABLES

_DB_PATH = os.getenv("DATABASE_URL", "./tutor.db")
_conn: Optional[aiosqlite.Connection] = None


async def get_db() -> aiosqlite.Connection:
    global _conn
    if _conn is None:
        _conn = await aiosqlite.connect(_DB_PATH)
        _conn.row_factory = aiosqlite.Row
        await _migrate(_conn)
    return _conn


async def _migrate(conn: aiosqlite.Connection) -> None:
    for statement in ALL_TABLES:
        await conn.execute(statement)
    await conn.commit()


async def close_db() -> None:
    global _conn
    if _conn is not None:
        await _conn.close()
        _conn = None
