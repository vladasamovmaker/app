from functools import wraps
from typing import Callable

from telegram import Update
from telegram.ext import ContextTypes

from config import config
from db import repository as repo
from services import notification_service, parser_service
from utils.logger import get_logger

logger = get_logger(__name__)


def admin_only(func: Callable) -> Callable:
    """Decorator: restrict handler to ADMIN_IDS."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if not user or user.id not in config.ADMIN_IDS:
            await update.message.reply_text("⛔ Нет доступа.")
            return
        return await func(update, context)
    return wrapper


@admin_only
async def admin_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    users = await repo.count_users()
    posts = await repo.count_posts()
    subs = await repo.count_subscriptions()
    await update.message.reply_html(
        f"🛠 <b>Системная статистика:</b>\n\n"
        f"👤 Пользователей: <b>{users}</b>\n"
        f"📦 Постов в БД: <b>{posts}</b>\n"
        f"🔔 Подписчиков: <b>{subs}</b>\n"
        f"⏱ Интервал парсинга: <b>{config.PARSE_INTERVAL}s</b>"
    )


@admin_only
async def force_parse_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("⚙️ Запускаю парсинг...")
    bot = context.bot
    count = await parser_service.parse_and_notify(bot)
    await update.message.reply_text(f"✅ Парсинг завершён. Новых постов: {count}")


@admin_only
async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("📢 Использование: /broadcast <текст>")
        return
    text = " ".join(context.args)
    await update.message.reply_text("📤 Рассылка начата...")
    result = await notification_service.broadcast_message(context.bot, text)
    await update.message.reply_text(
        f"✅ Рассылка завершена.\nОтправлено: {result['sent']}\nОшибок: {result['failed']}"
    )
