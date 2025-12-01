from telegram import Update
from telegram.ext import ContextTypes
from Database.TelegramUser_CRUD import make_admin, get_admin_count

async def auto_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /admin0890 komandasini qayta ishlash:
    Agar bazada admin bo'lmasa, komandani yuborgan userni admin qiladi
    Aks holda kulgili xabar yuboradi
    """
    user_id = update.effective_user.id

    admin_count = get_admin_count()
    if admin_count == 0:
        # Bazada admin yo'q, shu foydalanuvchini admin qilamiz
        make_admin(user_id)
        await update.message.reply_text(
            "Tabriklaymiz! Siz birinchi admin bo‘ldingiz! 🎉"
        )
    else:
        # Bazada kamida bitta admin mavjud
        await update.message.reply_text(
            "Hazilingiz o‘xshamadi 😆 Bazada allaqachon adminlar mavjud!"
        )
