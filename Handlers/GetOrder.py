import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import ConversationHandler, ContextTypes, MessageHandler, CallbackQueryHandler, filters
import os
from Handlers.Payment import send_price_buttons
from Keyboards.keyboards import get_back_cancel_keyboard, BACK_BUTTON, CANCEL_BUTTON, get_home_keyboard
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

DB_NAME = os.getenv("DB_NAME", "app.db")
ADMIN_CHANNEL_ID = -1003384632793  # Admin kanal ID sini yozing

WAIT_IMAGE, WAIT_CONFIRM, WAIT_ADD_DESC = range(3)


# =============================
# DATABASE FUNKSIYALAR
# =============================
def get_active_orders():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name, price FROM order_type WHERE is_active=1 ORDER BY price ASC")
    rows = c.fetchall()
    conn.close()
    return rows


def get_user_balance(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT balance FROM telegram_user WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0


# =============================
# BOSH MENYU
# =============================
async def user_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = await get_home_keyboard()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🔙 Bosh menyuga qaytildi",
        reply_markup=keyboard
    )
    return ConversationHandler.END


# =============================
# ZAKAZ BOSHLASH
# =============================
async def start_video_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name, price FROM order_type WHERE name=? AND is_active=1", (text,))
    row = c.fetchone()
    conn.close()

    if not row:
        return await fallback_handler(update, context)

    order_type_id, order_name, order_price = row

    # balans tekshirish
    balance = get_user_balance(user_id)
    if balance < order_price:
        await update.message.reply_text(
            f"❌ Hisobingizda mablag‘ yetarli emas! Tariff: {order_name} — {order_price} so‘m"
        )
        return await send_price_buttons(update, context)
    await context.bot.send_message(chat_id=update.effective_user.id, text=f"💰 Sizning balansingiz: {balance} so‘m va {balance // order_price} ta generatsiyaga yetadi")

    context.user_data["order_type"] = {
        "id": order_type_id,
        "name": order_name,
        "price": order_price
    }

    await update.message.reply_text(
        f"🖼 Rasm yuboring (tarif: {order_name} — {order_price} so‘m)",
        reply_markup=get_back_cancel_keyboard()
    )
    return WAIT_IMAGE


# =============================
# RASM QABUL QILISH
# =============================
async def receive_order_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text if update.message.text else ""
    if text in [BACK_BUTTON, CANCEL_BUTTON]:
        return await user_panel(update, context)

    if not update.message.photo:
        await update.message.reply_text("❌ Faqat rasm yuboring!", reply_markup=get_back_cancel_keyboard())
        return WAIT_IMAGE

    context.user_data["image_file_id"] = update.message.photo[-1].file_id

    return await send_confirm_menu(update, context)


# =============================
# TASDIQLASH MENYUSI
# =============================
async def send_confirm_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_type = context.user_data["order_type"]
    desc = context.user_data.get("description", "Tavsif berilmagan")

    confirm_btns = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data="confirm_yes"),
            InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")
        ],
        [InlineKeyboardButton("✍️ Tavsif qo‘shish", callback_data="add_desc")],
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="back_image")]
    ])

    await update.message.reply_text(
        f"📌 Zakazni tasdiqlaysizmi?\n"
        f"📦 Tarif: {order_type['name']}\n"
        f"💰 Narxi: {order_type['price']} so‘m\n"
        f"📝 Tavsif: {desc}",
        reply_markup=confirm_btns
    )

    return WAIT_CONFIRM


# =============================
# TASDIQLASH / TAVSIF QO‘SHISH
# =============================
async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "back_image":
        await query.message.reply_text(
            f"🖼 Rasm yuboring (tarif: {context.user_data['order_type']['name']})",
            reply_markup=get_back_cancel_keyboard()
        )
        return WAIT_IMAGE

    elif query.data == "add_desc":
        await query.message.delete()
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="✍️ Tavsif kiriting:",
            reply_markup=get_back_cancel_keyboard()
        )
        return WAIT_ADD_DESC

    elif query.data == "confirm_yes":
        order_type = context.user_data["order_type"]
        user_id = query.from_user.id

        # balansni yechish
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT balance FROM telegram_user WHERE user_id=?", (user_id,))
        balance = c.fetchone()[0]

        if balance < order_type["price"]:
            conn.close()
            await query.message.reply_text("❌ Hisobingizda mablag' yetarli emas!")
            return await user_panel(update, context)

        new_balance = balance - order_type["price"]
        c.execute("UPDATE telegram_user SET balance=? WHERE user_id=?", (new_balance, user_id))
        conn.commit()

        # zakazni bazaga saqlash
        import time
        c.execute(
            "INSERT INTO video_order (user_id, order_type_id, image_file_id, amount, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id,
             order_type["id"],
             context.user_data["image_file_id"],
             order_type["price"],
             "pending",
             time.strftime('%Y-%m-%d %H:%M:%S'))
        )
        conn.commit()
        
        # zakaz ID ni bazadan olish
        order_id = c.lastrowid
        conn.close()

        # admin kanalga yuborish
        desc = context.user_data.get("description", "Tavsif berilmagan")

        admin_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📥 Qabul qilish", callback_data=f"order_accept:{order_id}")]
        ])

        await context.bot.send_photo(
            chat_id=ADMIN_CHANNEL_ID,
            photo=context.user_data["image_file_id"],
            caption=(
                f"📩 *Yangi zakaz!*\n"
                f"👤 User ID: `{user_id}`\n"
                f"📦 Tarif: *{order_type['name']}*\n"
                f"💰 Narxi: {order_type['price']} so'm\n"
                f"📝 Tavsif: {desc}\n"
                f"🔖 Zakaz ID: `{order_id}`"
            ),
            reply_markup=admin_keyboard,
            parse_mode="Markdown"
        )

        await query.message.reply_text(
            f"<b>✅ Zakaz qabul qilindi!</b>\nTarif: {order_type['name']} — {order_type['price']} so'm\n<i>Ushbu jarayon 5 daqiqadan 5 soatgacha vaqt oralig'ida video yuboriladi. Iltimos, sabr qiling.</i>",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML"
        )

        return await user_panel(update, context)

    elif query.data == "cancel":
        return await user_panel(update, context)

    return WAIT_CONFIRM

# =============================
# TAVSIF QABUL QILISH
# =============================
async def add_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text in [BACK_BUTTON, CANCEL_BUTTON]:
        return await user_panel(update, context)

    context.user_data["description"] = text

    # tasdiqlash oynasiga qaytish
    return await send_confirm_menu(update, context)


# =============================
# FALLBACK
# =============================
async def fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Xato ma’lumot kiritildi yoki amal bekor qilindi.")
    return await user_panel(update, context)


# =============================
# CONVERSATION HANDLER
# =============================
active_orders = get_active_orders()
entry_handlers = [
    MessageHandler(filters.Regex(f"^({'|'.join([o[1] for o in active_orders])})$"), start_video_order)
]

video_order_conv = ConversationHandler(
    entry_points=entry_handlers,
    states={
        WAIT_IMAGE: [MessageHandler(filters.ALL, receive_order_image)],
        WAIT_CONFIRM: [CallbackQueryHandler(confirm_order, pattern="^(confirm_yes|cancel|add_desc|back_image)$")],
        WAIT_ADD_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_description)],
    },
    fallbacks=[MessageHandler(filters.ALL ^ filters.COMMAND, fallback_handler)],
    allow_reentry=True
)
