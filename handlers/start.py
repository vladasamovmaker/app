from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import repository as repo
from utils.logger import get_logger

logger = get_logger(__name__)


WELCOME_TEXT = """
🎁 <b>GiftHunter Bot</b> — твой личный охотник за подарками

Я мониторю лучшие маркетплейсы в реальном времени:
┌ 🔵 <b>Tonnel</b>
├ 🟣 <b>Portals</b>
└ 🟡 <b>MRKT</b>

Нахожу самые дешёвые лоты быстрее, чем их успевают купить.

<i>Выбери действие ниже 👇</i>
"""


def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔥 Свежие лоты", callback_data="latest"),
            InlineKeyboardButton("💸 Дешевле всего", callback_data="cheap"),
        ],
        [
            InlineKeyboardButton("🔍 Поиск", callback_data="search_prompt"),
            InlineKeyboardButton("📊 Статистика", callback_data="stats"),
        ],
        [
            InlineKeyboardButton("🔔 Уведомления", callback_data="sub_menu"),
        ],
    ])


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    try:
        await repo.upsert_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
        )
    except Exception as exc:
        logger.error(f"Failed to upsert user {user.id}: {exc}")

    await update.message.reply_html(
        WELCOME_TEXT.strip(),
        reply_markup=main_menu_keyboard(),
    )
