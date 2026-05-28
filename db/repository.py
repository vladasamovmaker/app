from datetime import datetime
from typing import Any, Optional

import aiosqlite

from db.database import get_db
from utils.logger import get_logger

logger = get_logger(__name__)


def _row_to_dict(row: aiosqlite.Row) -> dict:
    return dict(row)


# ── Users ──────────────────────────────────────────────────────────────────

async def upsert_user(telegram_id: int, username: Optional[str], first_name: Optional[str]) -> dict:
    db = await get_db()
    await db.execute(
        """
        INSERT INTO users (telegram_id, username, first_name)
        VALUES (?, ?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET
            username   = excluded.username,
            first_name = excluded.first_name,
            is_active  = 1
        """,
        (telegram_id, username, first_name),
    )
    await db.commit()
    async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cur:
        row = await cur.fetchone()
    return _row_to_dict(row)


async def get_all_active_users() -> list[dict]:
    db = await get_db()
    async with db.execute("SELECT * FROM users WHERE is_active = 1") as cur:
        rows = await cur.fetchall()
    return [_row_to_dict(r) for r in rows]


async def count_users() -> int:
    db = await get_db()
    async with db.execute("SELECT COUNT(*) FROM users WHERE is_active = 1") as cur:
        row = await cur.fetchone()
    return row[0]


# ── Posts ──────────────────────────────────────────────────────────────────

async def save_post(
    external_id: str,
    text: str,
    price: Optional[float],
    link: str,
    source: str,
    timestamp: datetime,
) -> Optional[dict]:
    """Insert post; returns None if duplicate."""
    db = await get_db()
    try:
        await db.execute(
            """
            INSERT INTO posts (external_id, text, price, link, source, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (external_id, text, price, link, source, timestamp.isoformat()),
        )
        await db.commit()
        async with db.execute(
            "SELECT * FROM posts WHERE external_id = ?", (external_id,)
        ) as cur:
            row = await cur.fetchone()
        return _row_to_dict(row)
    except aiosqlite.IntegrityError:
        return None  # duplicate


async def get_latest_posts(limit: int = 10) -> list[dict]:
    db = await get_db()
    async with db.execute(
        "SELECT * FROM posts ORDER BY timestamp DESC LIMIT ?", (limit,)
    ) as cur:
        rows = await cur.fetchall()
    return [_deserialize_post(_row_to_dict(r)) for r in rows]


async def get_posts_sorted_by_price(ascending: bool = True, limit: int = 10) -> list[dict]:
    order = "ASC" if ascending else "DESC"
    db = await get_db()
    async with db.execute(
        f"SELECT * FROM posts WHERE price IS NOT NULL ORDER BY price {order} LIMIT ?",
        (limit,),
    ) as cur:
        rows = await cur.fetchall()
    return [_deserialize_post(_row_to_dict(r)) for r in rows]


async def search_posts(keyword: str, limit: int = 10) -> list[dict]:
    db = await get_db()
    pattern = f"%{keyword}%"
    async with db.execute(
        "SELECT * FROM posts WHERE text LIKE ? ORDER BY timestamp DESC LIMIT ?",
        (pattern, limit),
    ) as cur:
        rows = await cur.fetchall()
    return [_deserialize_post(_row_to_dict(r)) for r in rows]


async def get_post_stats() -> dict:
    db = await get_db()
    async with db.execute(
        "SELECT COUNT(*) as total, AVG(price) as avg_price, MIN(price) as min_price, MAX(price) as max_price FROM posts"
    ) as cur:
        row = await cur.fetchone()
    return _row_to_dict(row)


async def count_posts() -> int:
    db = await get_db()
    async with db.execute("SELECT COUNT(*) FROM posts") as cur:
        row = await cur.fetchone()
    return row[0]


def _deserialize_post(post: dict) -> dict:
    if isinstance(post.get("timestamp"), str):
        try:
            post["timestamp"] = datetime.fromisoformat(post["timestamp"])
        except ValueError:
            post["timestamp"] = datetime.utcnow()
    return post


# ── Subscriptions ──────────────────────────────────────────────────────────

async def subscribe_user(telegram_id: int) -> bool:
    """Returns True if newly subscribed, False if already active."""
    db = await get_db()
    async with db.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)) as cur:
        user = await cur.fetchone()
    if not user:
        return False

    await db.execute(
        """
        INSERT INTO subscriptions (user_id)
        VALUES (?)
        ON CONFLICT(user_id) DO UPDATE SET is_active = 1
        """,
        (user["id"],),
    )
    await db.commit()
    return True


async def unsubscribe_user(telegram_id: int) -> bool:
    db = await get_db()
    async with db.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)) as cur:
        user = await cur.fetchone()
    if not user:
        return False
    await db.execute(
        "UPDATE subscriptions SET is_active = 0 WHERE user_id = ?", (user["id"],)
    )
    await db.commit()
    return True


async def get_subscribed_telegram_ids() -> list[int]:
    db = await get_db()
    async with db.execute(
        """
        SELECT u.telegram_id
        FROM subscriptions s
        JOIN users u ON u.id = s.user_id
        WHERE s.is_active = 1 AND u.is_active = 1
        """
    ) as cur:
        rows = await cur.fetchall()
    return [r["telegram_id"] for r in rows]


async def count_subscriptions() -> int:
    db = await get_db()
    async with db.execute("SELECT COUNT(*) FROM subscriptions WHERE is_active = 1") as cur:
        row = await cur.fetchone()
    return row[0]
