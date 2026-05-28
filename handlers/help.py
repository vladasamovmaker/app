from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

HELP_TEXT = """
📖 <b>GiftHunter — Справка</b>

<b>🎯 Основные команды:</b>
/start — главное меню
/latest — свежие лоты со всех площадок
/cheap — дешевле всего прямо сейчас
/expensive — самые дорогие лоты
/filter &lt;подарок&gt; — поиск по названию
/stats — статистика рынка

<b>🔔 Уведомления:</b>
/subscribe — получать новые лоты мгновенно
/unsubscribe — отключить уведомления

<b>📡 Источники данных:</b>
• Tonnel Marketplace
• Portals Marketplace  
• MRKT Marketplace

<i>Данные обновляются каждые 30 секунд</i>
"""


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ])
    await update.message.reply_html(HELP_TEXT.strip(), reply_markup=keyboard)
