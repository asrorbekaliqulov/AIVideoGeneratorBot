from telegram.ext import ConversationHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from Database.VideoOrder_CRUD import (
    get_video_order,
    update_video_order_status,
    update_video_order_video_file,
)
import sqlite3
import os
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

DB_NAME = os.getenv("DB_NAME", "app.db")

WAITING_VIDEO = 1
WAITING_EXTRA_TEXT = 2
WAITING_CANCEL_REASON = 3
WAITING_REFUND = 4


# ====================================================================================
# BUTTONS
# ====================================================================================

def admin_action_buttons(order_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎥 Videoni yuborish", callback_data=f"takeorder:{order_id}"),
            InlineKeyboardButton("❌ Bekor qilish", callback_data=f"cancelorder:{order_id}")
        ]
    ])


def skip_button(order_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Kerak emas", callback_data=f"skip:{order_id}")]
    ])


def refund_buttons(order_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Ha", callback_data=f"refund_yes:{order_id}"),
            InlineKeyboardButton("Yo‘q", callback_data=f"refund_no:{order_id}")
        ]
    ])


# ===================================================================================
# ADMIN ACTION — ACCEPT ORDER
# ===================================================================================
from telegram import InlineKeyboardButton, InlineKeyboardMarkup



async def accept_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_id = query.data.split(":")[1]
    order = get_video_order(order_id)

    admin_id = query.from_user.id

    channel_chat_id = query.message.chat_id      # Kanal chat_id
    channel_message_id = query.message.message_id  # Kanal message_id

    # --- 1) Kanaldagi xabarni tahrirlash ---
    try:
        await context.bot.edit_message_caption(
            chat_id=channel_chat_id,
            message_id=channel_message_id,
            caption=(
                "✔ **Zakaz qabul qilindi!**\n"
                f"User ID: `{order[1]}`\n"
                "Botga o'tib buyurtmani yakunlang."
            ),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🤖 Botga o'tish", url=f"https://t.me/{context.bot.username}")]
            ])
        )
    except Exception as e:
        print("Kanal xabar tahririda xatolik:", e)

    # --- 2) Adminning o'ziga xabar yuborish ---
    await context.bot.send_message(
        chat_id=admin_id,
        text=(
            f"📥 Zakaz qabul qilindi!\n"
            f"👤 User ID: `{order[1]}`\n"
            f"🔖 Zakaz ID: `{order[0]}`\n"
            f"💰 To‘lov: {order[6]} so‘m"
        ),
        parse_mode="Markdown",
        reply_markup=admin_action_buttons(order_id)
    )


# ===================================================================================
# ADMIN TAKES ORDER → SEND VIDEO
# ===================================================================================
async def take_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_id = query.data.split(":")[1]
    context.user_data["order_id"] = order_id

    await query.message.reply_text(
        "🎥 Video yuboring.\n❗ Faqat video yoki fayl yuboring."
    )

    return WAITING_VIDEO


async def admin_send_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_id = context.user_data.get("order_id")
    msg = update.message

    if not msg.video and not msg.document:
        await msg.reply_text("❗ Faqat video yuboring!")
        return WAITING_VIDEO

    file_id = msg.video.file_id if msg.video else msg.document.file_id

    # DB update
    update_video_order_video_file(order_id, file_id)

    await msg.reply_text(
        "➕ Qo‘shimcha matn yuborasizmi?",
        reply_markup=skip_button(order_id)
    )

    return WAITING_EXTRA_TEXT


# ===================================================================================
# SEND EXTRA TEXT
# ===================================================================================
async def extra_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    order_id = context.user_data["order_id"]

    order = get_video_order(order_id)

    description = (
        f"🎬 Buyurtmangiz tayyor!\n"
        f"Zakaz ID: {order[0]}\n\n"
        f"Admin izohi:\n{text}"
    )

    await context.bot.send_video(
        chat_id=order[1],
        video=order[4],
        caption=description
    )

    update_video_order_status(order[0], "done")

    await update.message.reply_text("✅ Zakaz topshirildi.")
    return ConversationHandler.END


async def skip_extra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_id = query.data.split(":")[1]
    order = get_video_order(order_id)

    await context.bot.send_video(
        chat_id=order[1],  # user_id is at index 1
        video=order[4],    # video_file_id is at index 4
        caption=f"🎬 Buyurtmangiz tayyor!\nZakaz ID: {order[0]}"
    )

    update_video_order_status(order[0], "done")

    await query.message.reply_text("📨 Matnsiz yuborildi.")
    return ConversationHandler.END


# ===================================================================================
# CANCEL ORDER
# ===================================================================================
async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_id = query.data.split(":")[1]
    context.user_data["order_id"] = order_id

    await query.message.reply_text("❌ Bekor qilish sababini yuboring:")
    return WAITING_CANCEL_REASON


async def cancel_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reason"] = update.message.text
    order_id = context.user_data["order_id"]

    await update.message.reply_text(
        "💸 To‘lov qaytarilsinmi?",
        reply_markup=refund_buttons(order_id)
    )

    return WAITING_REFUND


# ===================================================================================
# REFUND YES
# ===================================================================================
async def refund_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_id = query.data.split(":")[1]
    reason = context.user_data["reason"]

    order = get_video_order(order_id)

    # refund balans
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE telegram_user SET balance = balance + ? WHERE id=?", (order[6], order[1]))
    conn.commit()
    conn.close()

    update_video_order_status(order[0], "canceled", reason)
    await context.bot.send_message(
        chat_id=order[1],
        text=f"❌ Zakazingiz bekor qilindi!\nSabab: {reason}\n💰 {order[6]} so‘m qaytarildi."
    )

    await query.message.reply_text("♻️ Pul qaytarildi.")
    return ConversationHandler.END


# ===================================================================================
# REFUND NO
# ===================================================================================
async def refund_no(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_id = query.data.split(":")[1]
    reason = context.user_data["reason"]

    order = get_video_order(order_id)

    update_video_order_status(order[0], "canceled", reason)

    await context.bot.send_message(
        chat_id=order[1],
        text=f"❌ Zakaz bekor qilindi!\nSabab: {reason}"
    )

    await query.message.reply_text("❌ Bekor qilindi.")
    return ConversationHandler.END


# ===================================================================================
# FALLBACK
# ===================================================================================
async def fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❗ Noto‘g‘ri amal. Tugmalardan foydalaning.")
    return ConversationHandler.END


async def fallback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("❗ Bu amal mavjud emas.")
    return ConversationHandler.END


# ===================================================================================
# CONVERSATION HANDLER
# ===================================================================================
admin_video_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(take_order, pattern="^takeorder:"),
        CallbackQueryHandler(cancel_order, pattern="^cancelorder:")
    ],

    states={
        WAITING_VIDEO: [
            MessageHandler(filters.VIDEO | filters.Document.ALL, admin_send_video)
        ],
        WAITING_EXTRA_TEXT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, extra_text),
            CallbackQueryHandler(skip_extra, pattern="^skip:")
        ],
        WAITING_CANCEL_REASON: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, cancel_reason)
        ],
        WAITING_REFUND: [
            CallbackQueryHandler(refund_yes, pattern="^refund_yes:"),
            CallbackQueryHandler(refund_no, pattern="^refund_no:")
        ]
    },

    fallbacks=[
        MessageHandler(filters.ALL, fallback_handler),
        CallbackQueryHandler(fallback_query)
    ]
)
