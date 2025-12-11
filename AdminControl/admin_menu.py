from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes, CommandHandler, CallbackQueryHandler,
    ConversationHandler
)
import os
from Database.TelegramUser_CRUD import get_telegram_user
from Keyboards.keyboards import admin_panel_keyboard, admin_control_buttons
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

# States
(
    ADMIN_MENU,
    USER_MANAGEMENT,
    ADMIN_MANAGEMENT,
    BROADCAST,
    STATISTICS,
    ORDER_TYPE,
    PAYMENT,
    EXPORT
) = range(8)

# =====================================================
# /admin start
# =====================================================
async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel start, faqat adminlar uchun"""
    user = get_telegram_user(update.effective_user.id)
    if not user or not user[6]:  # is_admin = index 6
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Siz admin emassiz!")
        return ConversationHandler.END

    reply_markup = admin_panel_keyboard()
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Admin panel:", reply_markup=reply_markup)

# =====================================================
# CALLBACK HANDLER
# =====================================================
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    # =========================
    # User boshqaruvi
    # =========================
    if data == "user_management":
        await query.message.reply_text("User boshqaruvi paneli. (CRUD va filterlar shu yerda bo‘ladi)")

    # =========================
    # Admin boshqaruvi
    # =========================
    elif data == "admin_management":
        await query.message.reply_text("Admin boshqaruvi paneli. (Admin qo‘shish/o‘chirish)")

    # =========================
    # Xabar yuborish
    # =========================
    elif data == "broadcast":
        await query.message.reply_text("Xabar yuborish paneli. (Mass xabar shu yerda)")

    # =========================
    # Statistika
    # =========================
    elif data == "statistics":
        await query.message.reply_text("Statistika paneli. (Userlar, Zakazlar, To‘lovlar)")

    # =========================
    # Zakaz turi
    # =========================
    elif data == "order_type":
        await query.message.reply_text("Zakaz turlari paneli. (CRUD Zakaz turlari)")

    # =========================
    # Payment
    # =========================
    elif data == "payment":
        await query.message.reply_text("Payment paneli. (To‘lovlar monitoring, tasdiqlash)")

    # =========================
    # Export
    # =========================
    elif data == "export":
        await query.message.reply_text("Export paneli. (CSV / Excel export)")
        return EXPORT


async def admin_control_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin boshqaruvi menyusi"""
    reply_markup = admin_control_buttons()
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Admin boshqaruvi:", reply_markup=reply_markup)
