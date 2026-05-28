from typing import List, Optional

from db import repository as repo
from utils.logger import get_logger

logger = get_logger(__name__)


async def save_new_posts(raw_posts: List[dict]) -> List[dict]:
    """Persist new posts, skip duplicates. Returns only newly saved posts."""
    saved: List[dict] = []
    for p in raw_posts:
        try:
            result = await repo.save_post(
                external_id=p["id"],
                text=p["text"],
                price=p.get("price"),
                link=p.get("link", ""),
                source=p.get("source", "unknown"),
                timestamp=p["timestamp"],
            )
            if result is not None:
                saved.append(result)
        except Exception as exc:
            logger.error(f"Failed to save post {p.get('id')}: {exc}")
    if saved:
        logger.info(f"Saved {len(saved)} new posts (skipped {len(raw_posts) - len(saved)} duplicates)")
    return saved


async def get_latest(limit: int = 10) -> List[dict]:
    return await repo.get_latest_posts(limit=limit)


async def get_cheapest(limit: int = 10) -> List[dict]:
    return await repo.get_posts_sorted_by_price(ascending=True, limit=limit)


async def get_most_expensive(limit: int = 10) -> List[dict]:
    return await repo.get_posts_sorted_by_price(ascending=False, limit=limit)


async def search(keyword: str, limit: int = 10) -> List[dict]:
    if not keyword or len(keyword.strip()) < 2:
        return []
    return await repo.search_posts(keyword.strip(), limit=limit)


async def get_stats() -> dict:
    raw = await repo.get_post_stats()
    return {
        "total": raw.get("total", 0),
        "avg_price": raw.get("avg_price"),
        "min_price": raw.get("min_price"),
        "max_price": raw.get("max_price"),
    }
