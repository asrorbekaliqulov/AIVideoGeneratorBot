from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes, CommandHandler, CallbackQueryHandler,
    ConversationHandler
)
import os
from Database.TelegramUser_CRUD import get_telegram_user
from Keyboards.keyboards import admin_panel_keyboard

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
        await update.message.reply_text("Siz admin emassiz!")
        return ConversationHandler.END

    reply_markup = admin_panel_keyboard()
    await update.message.reply_text("Admin panel:", reply_markup=reply_markup)
    return ADMIN_MENU

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
        return USER_MANAGEMENT

    # =========================
    # Admin boshqaruvi
    # =========================
    elif data == "admin_management":
        await query.message.reply_text("Admin boshqaruvi paneli. (Admin qo‘shish/o‘chirish)")
        return ADMIN_MANAGEMENT

    # =========================
    # Xabar yuborish
    # =========================
    elif data == "broadcast":
        await query.message.reply_text("Xabar yuborish paneli. (Mass xabar shu yerda)")
        return BROADCAST

    # =========================
    # Statistika
    # =========================
    elif data == "statistics":
        await query.message.reply_text("Statistika paneli. (Userlar, Zakazlar, To‘lovlar)")
        return STATISTICS

    # =========================
    # Zakaz turi
    # =========================
    elif data == "order_type":
        await query.message.reply_text("Zakaz turlari paneli. (CRUD Zakaz turlari)")
        return ORDER_TYPE

    # =========================
    # Payment
    # =========================
    elif data == "payment":
        await query.message.reply_text("Payment paneli. (To‘lovlar monitoring, tasdiqlash)")
        return PAYMENT

    # =========================
    # Export
    # =========================
    elif data == "export":
        await query.message.reply_text("Export paneli. (CSV / Excel export)")
        return EXPORT

    return ADMIN_MENU

# =====================================================
# Conversation Handler
# =====================================================
admin_conv = ConversationHandler(
    entry_points=[CommandHandler("admin", admin_start)],
    states={
        ADMIN_MENU: [CallbackQueryHandler(admin_callback)],
        USER_MANAGEMENT: [],       # Keyin CRUD tugmalarini qo‘shishingiz mumkin
        ADMIN_MANAGEMENT: [],
        BROADCAST: [],
        STATISTICS: [],
        ORDER_TYPE: [],
        PAYMENT: [],
        EXPORT: [],
    },
    fallbacks=[]
)
