import asyncio

from telegram import Bot

from config import config
from parser.parser import run_parser
from services import post_service, notification_service
from utils.logger import get_logger

logger = get_logger(__name__)


async def parse_and_notify(bot: Bot) -> int:
    """Run one parse cycle: fetch → save → notify. Returns count of new posts."""
    logger.info("Starting parse cycle...")
    try:
        raw_posts = await run_parser()
        new_posts = await post_service.save_new_posts(raw_posts)
        if new_posts:
            await notification_service.notify_subscribers(bot, new_posts)
        logger.info(f"Parse cycle complete: {len(new_posts)} new posts saved")
        return len(new_posts)
    except Exception as exc:
        logger.error(f"Parse cycle error: {exc}", exc_info=True)
        return 0


async def start_scheduler(bot: Bot) -> None:
    """Background loop that runs parser every PARSE_INTERVAL seconds."""
    logger.info(f"Parser scheduler started (interval={config.PARSE_INTERVAL}s)")
    while True:
        await parse_and_notify(bot)
        await asyncio.sleep(config.PARSE_INTERVAL)
