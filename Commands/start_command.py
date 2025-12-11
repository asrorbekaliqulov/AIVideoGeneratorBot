from telegram.ext import ContextTypes, ConversationHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from Keyboards.keyboards import get_home_keyboard
from Database.TelegramUser_CRUD import create_telegram_user, get_telegram_user
import sqlite3
import os

DB_NAME = os.getenv("DB_NAME", "app.db")



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Botni ishga tushirish uchun komanda.
    """
    remove = ReplyKeyboardRemove()

    data = update.effective_user
    if update.callback_query:
        await update.callback_query.answer("Asosiy menyu")
        await update.callback_query.delete_message()

    reply_markup = await get_home_keyboard()
    user = get_telegram_user(data.id)
    if user:
        pass  # Foydalanuvchi bazada mavjud bo'lsa, yangilashni amalga oshirish mumkin
    else:

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, name, price FROM order_type WHERE is_active=1")
        row = c.fetchone()
        conn.close()

        if row:
            order_type_id, order_name, order_price = row
        else:
            order_type_id, order_name, order_price = None, None, 0
        is_save = create_telegram_user(data.id, data.first_name, data.username, balance=order_price)


    # === START VIDEO YUBORISH ===
    try:
        await context.bot.send_video(
            chat_id=update.effective_user.id,
            video="https://t.me/Hobbiy_bots/7",
            caption="<b>🎬 Eski fotosuratni qayta ishlash namunasi</b>",
            parse_mode="html"
        )
    except Exception as e:
        print("Xato {}".format(e))

    # === ASOSIY MENYU ===
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=("""
👋 Salom!

✨ Ushbu bot mumkin bo‘lmagan narsalarni hadya qilishi mumkin…
📷 Uning yordamida yoningda yo‘q bo‘lgan odamning tabassumini yana ko‘rishing mumkin.
        """
        ),
        parse_mode="html",
        reply_markup=reply_markup
    )

    return ConversationHandler.END


    