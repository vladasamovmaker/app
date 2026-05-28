import asyncio
import os
import sys

from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler

from config import config
from db.database import init_db, close_db
from db.models import create_tables
from handlers.admin import admin_stats_handler, broadcast_handler, force_parse_handler
from handlers.help import help_handler
from handlers.posts import (
    cheap_handler, expensive_handler, filter_handler,
    last_handler, latest_handler, stats_handler,
    subscribe_handler, unsubscribe_handler,
)
from handlers.start import start_handler
from handlers.callbacks import callback_handler
from services.parser_service import start_scheduler
from utils.logger import get_logger

logger = get_logger(__name__, config.LOG_LEVEL)


def build_application():
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("last", last_handler))
    app.add_handler(CommandHandler("latest", latest_handler))
    app.add_handler(CommandHandler("cheap", cheap_handler))
    app.add_handler(CommandHandler("expensive", expensive_handler))
    app.add_handler(CommandHandler("filter", filter_handler))
    app.add_handler(CommandHandler("stats", stats_handler))
    app.add_handler(CommandHandler("subscribe", subscribe_handler))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe_handler))
    app.add_handler(CommandHandler("admin_stats", admin_stats_handler))
    app.add_handler(CommandHandler("force_parse", force_parse_handler))
    app.add_handler(CommandHandler("broadcast", broadcast_handler))

    # Inline keyboard callbacks
    app.add_handler(CallbackQueryHandler(callback_handler))

    return app


async def main() -> None:
    config.validate()
    logger.info("Initializing database...")
    await init_db()
    await create_tables()

    app = build_application()
    scheduler_task = asyncio.create_task(start_scheduler(app.bot))

    logger.info("Bot starting...")
    try:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        logger.info("Bot is running!")
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown signal received")
    finally:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        await close_db()
        logger.info("Bot stopped cleanly")


if __name__ == "__main__":
    asyncio.run(main())
