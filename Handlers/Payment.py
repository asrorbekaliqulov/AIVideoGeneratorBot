import sqlite3
import os
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from tspay import TsPayClient
from Database.TelegramUser_CRUD import get_telegram_user, get_user_balance
from tspay.exceptions import TsPayError

DB_NAME = os.getenv("DB_NAME", "app.db")
SHOP_ACCESS_TOKEN = os.getenv("SHOP_ACCESS_TOKEN", "63Hj6VlMuefK7gJEh5jO84dtbWqjQ_UoxrrlLMbK4BY")

client = TsPayClient()

WAIT_PRICE, WAIT_CONFIRM = range(2)


# -------------------------
# USER PANEL FUNKSIYASI
# -------------------------
async def show_user_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, text="🏠 Asosiy panelga qaytdingiz"):
    keyboard = [
        [InlineKeyboardButton("🪄 Generatsiyalarni sotib olish", callback_data="gen_buy")],
    ]
    kb = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=kb)
    else:
        await update.message.reply_text(text, reply_markup=kb)


# -------------------------
# HELPERS
# -------------------------
def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, balance FROM telegram_user WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def get_active_order():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name, price FROM order_type WHERE is_active=1 ORDER BY id ASC LIMIT 1")
    row = c.fetchone()
    conn.close()
    return row

def create_payment(user_id, amount, cheque_id, order_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT INTO payment (user_id, amount, status, created_at, cheque_id) VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, "pending", datetime.now().isoformat(), cheque_id)
    )
    payment_id = c.lastrowid
    conn.commit()
    conn.close()
    return payment_id

# -------------------------
# GENERATSIYA SOTIB OLISH
# -------------------------
async def send_price_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_row = get_user(update.effective_user.id)
    if not user_row:
        return await show_user_panel(update, context, "❌ Siz ro‘yxatdan o‘tmagansiz. /start")

    order = get_active_order()
    if not order:
        return await show_user_panel(update, context, "⚠️ Faol zakaz turi topilmadi!")

    order_id, order_name, order_price = order
    context.user_data["order"] = {"id": order_id, "name": order_name, "price": order_price}

    # 🆕 User balansini olish
    balance = get_user_balance(update.effective_user.id)

    multipliers = [1, 3, 5, 10]
    buttons = [
        [InlineKeyboardButton(f"{m} ta generatsiya – {order_price * m} so'm", callback_data=f"price_{order_id}_{order_price * m}")]
        for m in multipliers
    ]
    buttons.append([InlineKeyboardButton("🏠 Bekor qilish", callback_data="cancel")])

    kb = InlineKeyboardMarkup(buttons)

    text = (
        f"💳 Zakaz: *{order_name}*\n"
        f"💰 Sizning balansingiz: *{balance} so‘m*\n\n"
        f"Quyidagi narxlardan birini tanlang:"
    )

    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")

    return WAIT_PRICE

# -------------------------
# NARX TANLANDI
# -------------------------
async def price_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, order_id, price = query.data.split("_")
    price = int(price)

    user_row = get_user(query.from_user.id)
    if not user_row:
        return await show_user_panel(update, context, "❌ Siz ro‘yxatdan o‘tmagansiz. /start")

    user_id, balance = user_row
    order_id = int(order_id)

    try:
        transaction = client.create_transaction(
            amount=price,
            redirect_url=f"https://t.me/{context.bot.username}",
            comment=f"User ID: {query.from_user.first_name} | @{query.from_user.username}",
            access_token=SHOP_ACCESS_TOKEN
        )
    except TsPayError as e:
        return await show_user_panel(update, context, f"❌ To‘lov yaratishda xatolik: {e}")

    payment_id = create_payment(user_id, price, transaction["cheque_id"], order_id)
    context.user_data["payment_id"] = payment_id

    buttons = [
        [InlineKeyboardButton("💳 To‘lash", url=transaction["payment_url"])],
        [InlineKeyboardButton("✅ To‘ladim", callback_data=f"paid_{payment_id}")],
        [InlineKeyboardButton("🏠 Bekor qilish", callback_data="cancel")]
    ]

    await query.message.edit_text(
        f"💳 Summa: {price} so'm\nTo‘lovni amalga oshiring:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

    return WAIT_CONFIRM


# -------------------------
# TO'LADIM → TEKSHIRISH
# -------------------------
async def paid_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    payment_id = int(query.data.split("_")[1])

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT cheque_id, user_id, amount, status FROM payment WHERE id=?", (payment_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return await show_user_panel(update, context, "❌ To‘lov topilmadi!")

    cheque_id, user_id, amount, status = row

    try:
        check = client.check_transaction(access_token=SHOP_ACCESS_TOKEN, cheque_id=cheque_id)
        print(check)
    except TsPayError:
        return await show_user_panel(update, context, "❌ Tekshirishda xatolik!")

    if check["status"] != "success":
        return await show_user_panel(update, context, "ℹ️ To‘lov hali tasdiqlanmagan.")

    # Tasdiqlangan → balansga qo‘shish
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE payment SET status='success', confirmed_at=? WHERE id=?", (datetime.now().isoformat(), payment_id))
    c.execute("UPDATE telegram_user SET balance = balance + ? WHERE id=?", (amount, user_id))
    conn.commit()
    conn.close()

    return await show_user_panel(update, context, f"✅ To‘lov tasdiqlandi! +{amount} so‘m qo‘shildi.")


# -------------------------
# BEKOR QILISH
# -------------------------
async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await show_user_panel(update, context, "❌ Amal bekor qilindi.")


# -------------------------
# HANDLERS
# -------------------------
send_price_button = MessageHandler(filters.Regex("^🪄 Generatsiyalarni sotib olish$"), send_price_buttons)
price_handler = CallbackQueryHandler(price_selected, pattern="^price_\\d+_\\d+$")
paid_handler = CallbackQueryHandler(paid_selected, pattern="^paid_\\d+$")
cancel_handler = CallbackQueryHandler(cancel_order, pattern="^cancel$")
menu_handler = CallbackQueryHandler(send_price_buttons, pattern="^gen_buy$")




