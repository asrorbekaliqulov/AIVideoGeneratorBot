from telegram.ext import ContextTypes, ConversationHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from Keyboards.keyboards import get_home_keyboard
from Database.TelegramUser_CRUD import create_telegram_user, get_telegram_user



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
        is_save = create_telegram_user(data.id, data.first_name, data.username)


    # === ADMIN uchun alohida xabar ===
    # if user and user.is_admin:
    #     await context.bot.send_message(
    #         chat_id=update.effective_user.id,
    #         text="<b>Main Menu 🖥\n<tg-spoiler>/admin_panel</tg-spoiler></b>",
    #         reply_markup=remove,
    #         parse_mode="html"
    #     )

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


    