from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import config
from db import repository as repo
from services import post_service
from utils.helpers import format_posts_list, format_stats
from utils.logger import get_logger

logger = get_logger(__name__)
MAX = config.MAX_POSTS_PER_PAGE


def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ])


def nav_keyboard(has_more: bool = False, offset: int = 0, action: str = "latest"):
    buttons = []
    if has_more:
        buttons.append(InlineKeyboardButton("➡️ Ещё", callback_data=f"{action}:{offset + MAX}"))
    buttons.append(InlineKeyboardButton("🏠 Меню", callback_data="main_menu"))
    return InlineKeyboardMarkup([buttons])


async def latest_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    posts = await post_service.get_latest(limit=MAX)
    text = format_posts_list(posts, "🔥 <b>Свежие лоты</b>")
    await update.message.reply_html(
        text,
        reply_markup=nav_keyboard(len(posts) == MAX, 0, "latest"),
        disable_web_page_preview=True,
    )


async def last_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await latest_handler(update, context)


async def cheap_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    posts = await post_service.get_cheapest(limit=MAX)
    if not posts:
        await update.message.reply_html(
            "😔 <b>Лотов с ценами пока нет</b>\n\nПодожди немного — парсер работает!",
            reply_markup=back_keyboard(),
        )
        return
    text = format_posts_list(posts, "💸 <b>Самые дешёвые лоты</b>")
    await update.message.reply_html(text, reply_markup=back_keyboard(), disable_web_page_preview=True)


async def expensive_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    posts = await post_service.get_most_expensive(limit=MAX)
    if not posts:
        await update.message.reply_html(
            "😔 <b>Лотов с ценами пока нет</b>",
            reply_markup=back_keyboard(),
        )
        return
    text = format_posts_list(posts, "📈 <b>Самые дорогие лоты</b>")
    await update.message.reply_html(text, reply_markup=back_keyboard(), disable_web_page_preview=True)


async def filter_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_html(
            "🔍 <b>Поиск по названию</b>\n\n"
            "Использование:\n<code>/filter Plush Peach</code>",
            reply_markup=back_keyboard(),
        )
        return
    keyword = " ".join(context.args)
    posts = await post_service.search(keyword, limit=MAX)
    text = format_posts_list(posts, f'🔍 <b>Результаты: «{keyword}»</b>')
    await update.message.reply_html(text, reply_markup=back_keyboard(), disable_web_page_preview=True)


async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    s = await post_service.get_stats()
    users = await repo.count_users()
    subs = await repo.count_subscriptions()
    text = format_stats(s, users, subs)
    await update.message.reply_html(text, reply_markup=back_keyboard())


async def subscribe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    ok = await repo.subscribe_user(user.id)
    if ok:
        await update.message.reply_html(
            "🔔 <b>Уведомления включены!</b>\n\n"
            "Буду присылать новые лоты сразу как они появятся.\n"
            "<i>Чтобы отключить — /unsubscribe</i>",
            reply_markup=back_keyboard(),
        )
    else:
        await update.message.reply_html(
            "⚠️ Сначала нажми /start для регистрации.",
            reply_markup=back_keyboard(),
        )


async def unsubscribe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    await repo.unsubscribe_user(user.id)
    await update.message.reply_html(
        "🔕 <b>Уведомления отключены</b>\n\n"
        "<i>Включить снова — /subscribe</i>",
        reply_markup=back_keyboard(),
    )
