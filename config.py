import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class Config:
    BOT_TOKEN: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    PARSE_INTERVAL: int = int(os.getenv("PARSE_INTERVAL", "30"))
    ADMIN_IDS: List[int] = field(
        default_factory=lambda: [
            int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()
        ]
    )
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/bot.db")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    MAX_POSTS_PER_PAGE: int = int(os.getenv("MAX_POSTS_PER_PAGE", "10"))
    NOTIFICATION_RETRY_ATTEMPTS: int = 3
    NOTIFICATION_RETRY_DELAY: float = 2.0

    def validate(self) -> None:
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN environment variable is required")


config = Config()
