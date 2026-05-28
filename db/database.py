import os
from typing import AsyncGenerator

import aiosqlite

from config import config
from utils.logger import get_logger

logger = get_logger(__name__)

_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db


async def init_db() -> None:
    global _db
    os.makedirs(os.path.dirname(config.DATABASE_PATH) or ".", exist_ok=True)
    _db = await aiosqlite.connect(config.DATABASE_PATH)
    _db.row_factory = aiosqlite.Row
    await _db.execute("PRAGMA journal_mode=WAL")
    await _db.execute("PRAGMA foreign_keys=ON")
    logger.info(f"Database connected: {config.DATABASE_PATH}")


async def close_db() -> None:
    global _db
    if _db:
        await _db.close()
        _db = None
        logger.info("Database connection closed")
