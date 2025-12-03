from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
)
from Database.OrderType_CRUD import (
    create_order_type, get_order_type, get_all_order_types,
    update_order_type, delete_order_type
)
from Keyboards.keyboards import admin_panel_keyboard, get_back_cancel_keyboard, BACK_BUTTON, CANCEL_BUTTON
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

(
    SELECT_ACTION,
    ADD_ORDER_NAME,
    ADD_ORDER_PRICE,
    ADD_ORDER_DESC,
    UPDATE_ORDER_NAME,
    UPDATE_ORDER_PRICE,
    UPDATE_ORDER_DESC
) = range(7)

# Admin panelga qaytarish helper
async def go_to_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = admin_panel_keyboard()
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Admin panelga qaytdingiz:",
                                   reply_markup=keyboard)
    return ConversationHandler.END


# ==========================
# START CALLBACK
# ==========================
async def zakaz_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Qo'shish", callback_data="add_order")],
        [InlineKeyboardButton("📋 Zakazlar", callback_data="list_orders")]
    ]
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Zakaz turini boshqarish:",
                                   reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_ACTION


# ==========================
# CALLBACK HANDLER
# ==========================
async def zakaz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data in ["back", "cancel"]:
        await query.message.reply_text("Amal bekor qilindi.")
        return await go_to_admin_panel(update, context)

    # Qo'shish
    if data == "add_order":
        await query.message.reply_text("Yangi zakaz turining nomini yozing:",
                                       reply_markup=get_back_cancel_keyboard())
        return ADD_ORDER_NAME

    # Ro'yxat
    elif data == "list_orders":
        orders = get_all_order_types(active_only=False)
        if not orders:
            await query.message.reply_text("Hech qanday zakaz turi mavjud emas.")
            return SELECT_ACTION

        keyboard = []
        row = []
        for i, order in enumerate(orders, start=1):
            row.append(InlineKeyboardButton(order[1], callback_data=f"view_{order[0]}"))
            if i % 3 == 0:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("➕ Qo'shish", callback_data="add_order")])
        await query.message.reply_text("Zakaz turlari:", reply_markup=InlineKeyboardMarkup(keyboard))
        return SELECT_ACTION

    # View / Edit / Delete / Toggle
    elif data.startswith("view_"):
        order_id = int(data.split("_")[1])
        order = get_order_type(order_id)
        if not order:
            await query.message.reply_text("Zakaz topilmadi.")
            return SELECT_ACTION
        text = f"**Zakaz turi:** {order[1]}\n**Narxi:** {order[3]} so'm\n**Ta'rif:** {order[4]}\n**Faol:** {'✅' if order[5] else '❌'}"
        keyboard = [
            [
                InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"edit_{order_id}"),
                InlineKeyboardButton("🛑 Faolsizlantirish", callback_data=f"toggle_{order_id}"),
                InlineKeyboardButton("❌ O'chirish", callback_data=f"delete_{order_id}")
            ]
        ]
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return SELECT_ACTION

    # Edit
    elif data.startswith("edit_"):
        order_id = int(data.split("_")[1])
        context.user_data["edit_order_id"] = order_id
        await query.message.reply_text("Zakaz turining yangi nomini yozing:",
                                       reply_markup=get_back_cancel_keyboard())
        return UPDATE_ORDER_NAME

    # Toggle
    elif data.startswith("toggle_"):
        order_id = int(data.split("_")[1])
        order = get_order_type(order_id)
        new_status = 0 if order[5] else 1
        update_order_type(order_id, is_active=new_status)
        await query.message.reply_text(f"Zakaz turi {'faol' if new_status else 'no-faol'} qilindi.")
        return SELECT_ACTION

    # Delete
    elif data.startswith("delete_"):
        order_id = int(data.split("_")[1])
        delete_order_type(order_id)
        await query.message.reply_text("Zakaz turi o‘chirildi.")
        return SELECT_ACTION

    # Noma'lum callback
    else:
        await query.message.reply_text("Bekor qilindi.")
        return await go_to_admin_panel(update, context)


# ==========================
# ADD ORDER HANDLERS
# ==========================
async def add_order_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text in [BACK_BUTTON, CANCEL_BUTTON]:
        await update.message.reply_text("Amal bekor qilindi.")
        return await go_to_admin_panel(update, context)
    context.user_data["new_order_name"] = text
    await update.message.reply_text("Narxini kiriting (so‘m):", reply_markup=get_back_cancel_keyboard())
    return ADD_ORDER_PRICE

async def add_order_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text in [BACK_BUTTON, CANCEL_BUTTON]:
        await update.message.reply_text("Amal bekor qilindi.")
        return await go_to_admin_panel(update, context)
    if not text.isdigit():
        await update.message.reply_text("Iltimos raqam kiriting:", reply_markup=get_back_cancel_keyboard())
        return ADD_ORDER_PRICE
    context.user_data["new_order_price"] = int(text)
    await update.message.reply_text("Ta'rifini yozing:", reply_markup=get_back_cancel_keyboard())
    return ADD_ORDER_DESC

async def add_order_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text in [BACK_BUTTON, CANCEL_BUTTON]:
        await update.message.reply_text("Amal bekor qilindi.")
        return await go_to_admin_panel(update, context)
    name = context.user_data.get("new_order_name")
    price = context.user_data.get("new_order_price")
    description = text
    create_order_type(name=name, price=price, description=description)
    await update.message.reply_text(f"Zakaz turi '{name}' qo‘shildi.")
    return await go_to_admin_panel(update, context)


# ==========================
# UPDATE ORDER HANDLERS
# ==========================
async def update_order_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text in [BACK_BUTTON, CANCEL_BUTTON]:
        await update.message.reply_text("Amal bekor qilindi.")
        return await go_to_admin_panel(update, context)
    context.user_data["edit_order_name"] = text
    await update.message.reply_text("Narxini kiriting (so‘m):", reply_markup=get_back_cancel_keyboard())
    return UPDATE_ORDER_PRICE

async def update_order_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text in [BACK_BUTTON, CANCEL_BUTTON]:
        await update.message.reply_text("Amal bekor qilindi.")
        return await go_to_admin_panel(update, context)
    if not text.isdigit():
        await update.message.reply_text("Iltimos raqam kiriting:", reply_markup=get_back_cancel_keyboard())
        return UPDATE_ORDER_PRICE
    context.user_data["edit_order_price"] = int(text)
    await update.message.reply_text("Ta'rifini yozing:", reply_markup=get_back_cancel_keyboard())
    return UPDATE_ORDER_DESC

async def update_order_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text in [BACK_BUTTON, CANCEL_BUTTON]:
        await update.message.reply_text("Amal bekor qilindi.")
        return await go_to_admin_panel(update, context)
    order_id = context.user_data.get("edit_order_id")
    name = context.user_data.get("edit_order_name")
    price = context.user_data.get("edit_order_price")
    description = text
    update_order_type(order_id, name=name, price=price, description=description)
    await update.message.reply_text(f"Zakaz turi yangilandi: {name}")
    return await go_to_admin_panel(update, context)


# ==========================
# CONVERSATION HANDLER
# ==========================
zakaz_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(zakaz_start, pattern="^order_type$")],
    states={
        SELECT_ACTION: [CallbackQueryHandler(zakaz_callback)],
        ADD_ORDER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_order_name)],
        ADD_ORDER_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_order_price)],
        ADD_ORDER_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_order_desc)],
        UPDATE_ORDER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_order_name)],
        UPDATE_ORDER_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_order_price)],
        UPDATE_ORDER_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_order_desc)],
    },
    fallbacks=[
        MessageHandler(filters.Regex(f"^{CANCEL_BUTTON}$"), lambda u,c: go_to_admin_panel(u,c)),
        MessageHandler(filters.Regex(f"^{BACK_BUTTON}$"), lambda u,c: go_to_admin_panel(u,c))
    ],
    allow_reentry=True
)
