from db.database import get_db
from utils.logger import get_logger

logger = get_logger(__name__)

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY,
    telegram_id INTEGER UNIQUE NOT NULL,
    username    TEXT,
    first_name  TEXT,
    is_active   INTEGER DEFAULT 1,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_POSTS_TABLE = """
CREATE TABLE IF NOT EXISTS posts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT UNIQUE NOT NULL,
    text        TEXT NOT NULL,
    price       REAL,
    link        TEXT,
    source      TEXT,
    timestamp   TIMESTAMP NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_SUBSCRIPTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS subscriptions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_active   INTEGER DEFAULT 1,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
)
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_posts_timestamp ON posts(timestamp DESC)",
    "CREATE INDEX IF NOT EXISTS idx_posts_price ON posts(price)",
    "CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)",
    "CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id)",
]


async def create_tables() -> None:
    db = await get_db()
    async with db.executescript(
        f"""
        {CREATE_USERS_TABLE};
        {CREATE_POSTS_TABLE};
        {CREATE_SUBSCRIPTIONS_TABLE};
        {''.join(idx + ';' for idx in CREATE_INDEXES)}
        """
    ):
        pass
    await db.commit()
    logger.info("Database tables initialized")
