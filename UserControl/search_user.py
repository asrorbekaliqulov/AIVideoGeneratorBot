from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import sqlite3
from Database.VideoOrder_CRUD import get_order_count_by_user_id
from telegram.ext import Updater
import os

DB_NAME = os.getenv("DB_NAME", "app.db")

# Function to search user by ID or username
async def search_user(update: Update, context) -> int:
    await context.bot.send_message(chat_id=update.effective_user.id, text="Iltimos, user ID yoki username kiriting:")
    return 1

async def get_user_stats(update: Update, context) -> int:
    user_input = update.message.text
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Check if input is an ID or username
    if user_input.isdigit():
        cursor.execute("SELECT * FROM telegram_user WHERE user_id = ?", (user_input,))
    else:
        cursor.execute("SELECT * FROM telegram_user WHERE username = ?", (user_input,))

    user = cursor.fetchone()
    order_count = get_order_count_by_user_id(user[1]) if user else 0
    if user:
        response = (f"User ID: {user[1]}\n"
                    f"Username: {user[3]}\n"
                    f"Zakazlar soni: {order_count}\n"
        )       
        # Inline buttons for additional actions
        keyboard = [
            [InlineKeyboardButton("Buyurtmalari", callback_data=f"userorders_{user[1]}")],
            # [InlineKeyboardButton("To'lov tarixi", callback_data=f"payment_{user[1]}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(response, reply_markup=reply_markup)
    else:
        response = "Foydalanuvchi topilmadi."
        await update.message.reply_text(response)
    await update.message.reply_text(text="Admin panelga qaytish uchun /admin buyrug'ini yuboring.")
    conn.close()
    return ConversationHandler.END

async def cancel(update: Update, context) -> int:
    await update.message.reply_text("Qidirish bekor qilindi.")
    return ConversationHandler.END


search_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(search_user, pattern="^search_user$")],
    states={
        1: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_user_stats)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)

async def handle_user_orders(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    user_id = query.data.split("_")[1]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, amount, status FROM video_order WHERE user_id = ?", (user_id,))
    orders = cursor.fetchall()
    conn.close()

    if orders:
        orders_text = "Foydalanuvchining buyurtmalari:\n\n"
        keyboard = []
        for order in orders:
            orders_text += (f"Zakaz ID: {order[0]}\n"
                            f"Miqdor: {order[1]}\n"
                            f"Holat: {order[2]}\n\n")
            
            # Qabul qilish tugmasini faqat pending holatda ko'rsatish
            if order[2].lower() != "done":
                keyboard.append([InlineKeyboardButton(f"Qabul qilish (ID: {order[0]})", callback_data=f"order_accept:{order[0]}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        await query.edit_message_text(orders_text, reply_markup=reply_markup)
    else:
        orders_text = "Foydalanuvchining buyurtmalari topilmadi."
        await query.edit_message_text(orders_text)
    
    return ConversationHandler.END