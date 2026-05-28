import asyncio
from typing import List

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError

from config import config
from db import repository as repo
from utils.helpers import format_post
from utils.logger import get_logger

logger = get_logger(__name__)


def _gift_keyboard(link: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Купить", url=link)],
    ])


async def _send_with_retry(bot: Bot, telegram_id: int, text: str, keyboard=None) -> bool:
    for attempt in range(1, config.NOTIFICATION_RETRY_ATTEMPTS + 1):
        try:
            await bot.send_message(
                chat_id=telegram_id,
                text=text,
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=keyboard,
            )
            return True
        except TelegramError as exc:
            if "blocked" in str(exc).lower() or "deactivated" in str(exc).lower():
                return False
            if attempt < config.NOTIFICATION_RETRY_ATTEMPTS:
                await asyncio.sleep(config.NOTIFICATION_RETRY_DELAY * attempt)
    return False


async def notify_subscribers(bot: Bot, new_posts: List[dict]) -> None:
    if not new_posts:
        return
    subscriber_ids = await repo.get_subscribed_telegram_ids()
    if not subscriber_ids:
        return

    logger.info(f"Notifying {len(subscriber_ids)} subscribers about {len(new_posts)} new posts")

    for post in new_posts:
        link = post.get("link", "")
        keyboard = _gift_keyboard(link) if link else None
        message = f"🆕 <b>Новый лот!</b>\n\n{format_post(post)}"
        tasks = [_send_with_retry(bot, tid, message, keyboard) for tid in subscriber_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        success = sum(1 for r in results if r is True)
        logger.info(f"Delivered to {success}/{len(subscriber_ids)} subscribers")
        await asyncio.sleep(0.3)


async def broadcast_message(bot: Bot, text: str) -> dict:
    users = await repo.get_all_active_users()
    sent, failed = 0, 0
    for user in users:
        ok = await _send_with_retry(bot, user["telegram_id"], text)
        if ok:
            sent += 1
        else:
            failed += 1
        await asyncio.sleep(0.05)
    return {"sent": sent, "failed": failed}
