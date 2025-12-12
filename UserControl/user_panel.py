from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import sqlite3



async def user_management_panel(update: Update, context) -> int:
    """Foydalanuvchi boshqaruv paneli"""
    
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text="👤 Foydalanuvchi boshqaruv paneliga xush kelibsiz!",
         reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Foydalanuvchini qidirish", callback_data="search_user")],
            # [InlineKeyboardButton("📦 Zakazlarni yuborish", callback_data="send_order")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_main_menu")]
        ])
    )
    