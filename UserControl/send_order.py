from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from Database.TelegramUser_CRUD import get_user_by_id, get_user_by_username, get_user_orders, save_video_file_id
from telegram.ext import ConversationHandler

async def user_search_for_send_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin paneldan zakaz videosini foydalanuvchiga yuboradi"""
    
    await update.message.reply_text("🔍 Foydalanuvchi username yoki ID raqamini kiriting:")

    return "AWAITING_USER_INPUT"
  
async def process_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    user = None

    # Foydalanuvchini ID bo'yicha qidirish
    if user_input.isdigit():
        user = get_user_by_id(int(user_input))
    else:
        # Foydalanuvchini username bo'yicha qidirish
        if user_input.startswith("@"):
            user_input = user_input[1:]
        user = get_user_by_username(user_input)
    
    if not user:
        await update.message.reply_text("❌ Foydalanuvchi topilmadi. Iltimos, to'g'ri username yoki ID kiriting.")
        return "AWAITING_USER_INPUT"
    
    user_orders = get_user_orders(user.id)
    if not user_orders:
        await update.message.reply_text("❌ Ushbu foydalanuvchida zakazlar mavjud emas.")
        return "END"

    context.user_data['target_user_id'] = user.id
    orders_text = "\n".join([f"📦 Zakaz ID: {order.id}, Holati: {order.status}" for order in user_orders])
    
    if len(user_orders) == 1:
        order = user_orders[0]
        caption = f"📦 Zakaz ID: {order.id}\n📊 Holati: {order.status}\n📝 Tavsif: {order.description}"
        
        if order.status == "accepted":
            # Qabul qilingan zakaz - tugma chiqmasin
            if order.video_file_id:
                await update.message.reply_video(video=order.video_file_id, caption=caption)
            else:
                await update.message.reply_text(caption)
        else:
            # Qabul qilinmagan zakaz - qabul qilish tugmasi bilan
            if order.video_file_id:
                await update.message.reply_video(video=order.video_file_id, caption=caption, reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Zakazni qabul qilish", callback_data=f"accept_order_{order.id}")],
                    [InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_search")]
                ]))
            else:
                await update.message.reply_text(caption, reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Zakazni qabul qilish", callback_data=f"accept_order_{order.id}")],
                    [InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_search")]
                ]))
        return "AWAITING_ORDER_ACTION"
    else:
        await update.message.reply_text("📋 Zakazlar ro'yxati:\n\n" + orders_text + "\n\n👇 Raqamni tanlang:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(str(i+1), callback_data=f"select_order_{user_orders[i].id}")] for i in range(len(user_orders))
        ]))
        return "AWAITING_ORDER_SELECTION"


async def handle_accept_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Zakazni qabul qilish"""
    query = update.callback_query
    await query.answer()
    
    order_id = query.data.split("_")[2]
    # Zakaz statusini "accepted" qilib o'zgartrish
    update_order_status(order_id, "accepted")
    
    await query.edit_message_caption(caption="✅ Zakaz muvaffaqiyatli qabul qilindi!")
    return "END"


async def handle_back_to_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Orqaga tugmasi"""
    query = update.callback_query
    await query.answer()
    await query.delete_message()
    
    await update.effective_chat.send_message("🔍 Foydalanuvchi username yoki ID raqamini kiriting:")
    return "AWAITING_USER_INPUT"

    # States
    AWAITING_USER_INPUT, AWAITING_ORDER_ACTION, AWAITING_ORDER_SELECTION = range(3)

    # Conversation handler
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', user_search_for_send_order)],
        states={
            AWAITING_USER_INPUT: [MessageHandler(Filters.text & ~Filters.command, process_user_input)],
            AWAITING_ORDER_ACTION: [CallbackQueryHandler(handle_accept_order, pattern=r'accept_order_\d+'),
                                    CallbackQueryHandler(handle_back_to_search, pattern='back_to_search')],
            AWAITING_ORDER_SELECTION: [CallbackQueryHandler(process_user_input, pattern=r'select_order_\d+')]
        },
        fallbacks=[CommandHandler('cancel', handle_back_to_search)],
    )
