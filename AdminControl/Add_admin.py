from telegram import Update, KeyboardButtonRequestUsers, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from Database.TelegramUser_CRUD import make_admin, get_admin_count, is_user_admin

async def auto_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /admin0890 komandasini qayta ishlash:
    Agar bazada admin bo'lmasa, komandani yuborgan userni admin qiladi
    Aks holda kulgili xabar yuboradi
    """
    user_id = update.effective_user.id

    admin_count = get_admin_count()
    if admin_count < 2:
        # Bazada admin yo'q, shu foydalanuvchini admin qilamiz
        make_admin(user_id)
        await update.message.reply_text(
            "Tabriklaymiz! Siz admin bo‘ldingiz! 🎉"
        )
    else:
        # Bazada kamida bitta admin mavjud
        await update.message.reply_text(
            "Hazilingiz o‘xshamadi 😆 Bazada allaqachon adminlar mavjud!"
        )


async def Admin_Add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if is_user_admin(user_id):
        users_keyboard = [[
            KeyboardButton(text="Yangi adminni tanlang", request_users=KeyboardButtonRequestUsers(
                request_id=1,
                user_is_bot=False,
                request_name=True
            ))
        ],
        [KeyboardButton(text="🔙 Orqаga")]]
        reply_markup = ReplyKeyboardMarkup(
            users_keyboard,
            one_time_keyboard=True,
            resize_keyboard=True
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Iltimos, yangi admin bo‘lishi kerak bo‘lgan foydalanuvchini quyidagi tugmani bosib tanlang:",
            reply_markup=reply_markup
        )

async def handle_new_admin_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.users_shared:
        user = update.message.users_shared.to_dict()
        new_admin_id = user['users'][0]['user_id']

        if is_user_admin(new_admin_id):
            await update.message.reply_text(f"Ushbu foydalanuvchi allaqachon admin hisoblanadi.")
        else:
            make_admin(new_admin_id)
            await context.bot.send_message(chat_id=new_admin_id, text="Siz endi admin bo‘ldingiz! 🎉")
            await update.message.reply_text(f"Foydalanuvchi endi admin bo‘ldi! 🎉")
    else:
        await update.message.reply_text("Iltimos, yangi adminni tanlash uchun tugmani bosing.")

async def lists_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Barcha adminlarni ro'yxatini ko'rsatadi
    """
    # Bu funksiyani keyinchalik amalga oshirish mumkin
    pass