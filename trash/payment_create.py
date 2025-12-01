from tspay import TsPayClient
from tspay.exceptions import TsPayError
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ApplicationBuilder, ContextTypes
from asgiref.sync import sync_to_async
from apps.Bot.models.TelegramBot import TelegramUser, Payment, OrderType
import os

PAYMENT_API_KEY = os.getenv("PAYMENT_API_KEY")
SHOP_ACCESS_TOKEN = os.getenv("SHOP_ACCESS_TOKEN")

client = TsPayClient()

# --- STEP 1: Zakaz tanlash ---
async def send_order_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    orders = await sync_to_async(list)(OrderType.objects.all())
    buttons = []
    for order in orders:
        text = f"{order.name}"
        buttons.append([InlineKeyboardButton(text, callback_data=f"order_{order.id}")])
    buttons.append([InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")])
    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("💰 Zakaz turini tanlang:", reply_markup=keyboard)

# --- ORDER TANLANGANDA ---
async def order_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    order_id = int(query.data.split("_")[1])
    order = await sync_to_async(OrderType.objects.get)(id=order_id)

    # Narx variantlarini yuborish
    await send_price_buttons(query, order)

# --- PRICE VARIANTI TANLANGANDA ---
async def price_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, order_id, price = query.data.split("_")
    order = await sync_to_async(OrderType.objects.get)(id=int(order_id))
    price = int(price)
    tg_user = query.from_user

    # Transaction yaratish
    try:
        transaction = client.create_transaction(
            amount=price,
            redirect_url=f"https://t.me/{context.bot.username}",
            comment=f"User ID: {tg_user.id} | Order: {order.name}",
            access_token=PAYMENT_API_KEY
        )
    except TsPayError as e:
        await query.message.reply_text(f"❌ To‘lov yaratishda xatolik: {e}")
        return

    # Bazaga saqlash
    try:
        user = await sync_to_async(TelegramUser.objects.get)(user_id=tg_user.id)
    except TelegramUser.DoesNotExist:
        await query.message.reply_text("❌ Siz ro‘yxatdan o‘tmagansiz. /start")
        return

    payment = await sync_to_async(Payment.objects.create)(
        user=user,
        amount=price,
        cheque_id=transaction['cheque_id'],
        status="pending",
        order_type=order
    )

    # To’lov tugmalari
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 To‘lovni amalga oshirish", url=transaction['payment_url'])],
        [InlineKeyboardButton("✅ To‘ladim", callback_data=f"paid_{payment.id}")],
        [InlineKeyboardButton("⬅️ Orqaga", callback_data=f"back_price_{order.id}")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")]
    ])

    await query.message.edit_text(
        f"💳 Zakaz: {order.name}\n💰 Summa: {price} so'm\n\n"
        "To‘lovni amalga oshirish uchun tugmani bosing:",
        reply_markup=keyboard
    )

# --- TO'LADIM BOSILSA ---
async def paid_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    payment_id = int(query.data.split("_")[1])
    payment = await sync_to_async(Payment.objects.get)(id=payment_id)

    # Transaction holatini tekshirish
    try:
        status = client.check_transaction(
            access_token=SHOP_ACCESS_TOKEN,
            cheque_id=payment.cheque_id
        )
    except TsPayError as e:
        await query.message.reply_text(f"❌ Tekshirishda xatolik: {e}")
        return

    if status["status"] == "paid":
        # Payment va user balance update
        await sync_to_async(Payment.objects.filter(id=payment_id).update)(status="success")
        user = payment.user
        user.balance += payment.amount
        await sync_to_async(user.save)()
        await query.message.edit_text(
            f"✅ To‘lov tasdiqlandi!\n💰 {payment.amount} so'm balansingizga qo‘shildi."
        )
    else:
        await query.message.reply_text("ℹ️ To‘lov hali bajarilmagan. Iltimos, keyinroq tekshiring.")

# --- ORQAGA NARX TANLASHGA ---
async def back_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    order_id = int(query.data.split("_")[2])
    order = await sync_to_async(OrderType.objects.get)(id=order_id)
    await send_price_buttons(query, order)

# --- ORQAGA ZAKAZ TANLASHGA ---
async def back_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await send_order_buttons(query, context)

# --- PRICE BUTTON GENERATOR ---
async def send_price_buttons(query, order):
    prices = [1,3,5,10]  # generatsiya variantlari
    buttons = []
    for p in prices:
        price_amount = order.price * p
        buttons.append([InlineKeyboardButton(f"{p} generatsiya - {price_amount} so'm", callback_data=f"price_{order.id}_{price_amount}")])
    buttons.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="back_order")])
    buttons.append([InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")])
    keyboard = InlineKeyboardMarkup(buttons)
    await query.message.edit_text(
        f"💳 Zakaz: {order.name}\nNarx variantini tanlang:",
        reply_markup=keyboard
    )

# --- BOT YURITISH ---
app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()


app.run_polling()
