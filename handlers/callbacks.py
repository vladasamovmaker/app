from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import config
from db import repository as repo
from services import post_service
from utils.helpers import format_posts_list, format_stats
from utils.logger import get_logger

logger = get_logger(__name__)
MAX = config.MAX_POSTS_PER_PAGE


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


def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ])


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "main_menu":
        await query.edit_message_text(
            "🎁 <b>GiftHunter</b> — выбери действие:",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )

    elif data == "latest" or data.startswith("latest:"):
        offset = int(data.split(":")[1]) if ":" in data else 0
        posts = await post_service.get_latest(limit=MAX)
        text = format_posts_list(posts, "🔥 <b>Свежие лоты</b>")
        buttons = []
        if len(posts) == MAX:
            buttons.append(InlineKeyboardButton("➡️ Ещё", callback_data=f"latest:{offset + MAX}"))
        buttons.append(InlineKeyboardButton("🏠 Меню", callback_data="main_menu"))
        await query.edit_message_text(
            text, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([buttons]),
            disable_web_page_preview=True,
        )

    elif data == "cheap":
        posts = await post_service.get_cheapest(limit=MAX)
        text = format_posts_list(posts, "💸 <b>Самые дешёвые лоты</b>")
        await query.edit_message_text(
            text, parse_mode="HTML",
            reply_markup=back_keyboard(),
            disable_web_page_preview=True,
        )

    elif data == "stats":
        s = await post_service.get_stats()
        users = await repo.count_users()
        subs = await repo.count_subscriptions()
        text = format_stats(s, users, subs)
        await query.edit_message_text(
            text, parse_mode="HTML",
            reply_markup=back_keyboard(),
        )

    elif data == "search_prompt":
        await query.edit_message_text(
            "🔍 <b>Поиск подарка</b>\n\n"
            "Отправь команду:\n"
            "<code>/filter Plush Peach</code>\n\n"
            "<i>Можно искать по части названия</i>",
            parse_mode="HTML",
            reply_markup=back_keyboard(),
        )

    elif data == "sub_menu":
        user = update.effective_user
        is_subbed = user.id in await repo.get_subscribed_telegram_ids()
        if is_subbed:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔕 Отключить уведомления", callback_data="unsubscribe")],
                [InlineKeyboardButton("🏠 Меню", callback_data="main_menu")],
            ])
            text = "🔔 <b>Уведомления включены</b>\n\nТы получаешь новые лоты мгновенно."
        else:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔔 Включить уведомления", callback_data="subscribe")],
                [InlineKeyboardButton("🏠 Меню", callback_data="main_menu")],
            ])
            text = "🔕 <b>Уведомления отключены</b>\n\nВключи чтобы получать лоты мгновенно."
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)

    elif data == "subscribe":
        user = update.effective_user
        await repo.subscribe_user(user.id)
        await query.edit_message_text(
            "🔔 <b>Уведомления включены!</b>\n\n"
            "Буду присылать новые лоты сразу как они появятся.",
            parse_mode="HTML",
            reply_markup=back_keyboard(),
        )

    elif data == "unsubscribe":
        user = update.effective_user
        await repo.unsubscribe_user(user.id)
        await query.edit_message_text(
            "🔕 <b>Уведомления отключены</b>\n\n"
            "<i>Включить снова можно через меню.</i>",
            parse_mode="HTML",
            reply_markup=back_keyboard(),
        )
