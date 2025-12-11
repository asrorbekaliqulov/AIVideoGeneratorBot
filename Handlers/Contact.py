from telegram import Update
from telegram.ext import ContextTypes
from Database.TelegramUser_CRUD import get_admin_users

async def contact_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admins = get_admin_users()

    if not admins:
        await update.message.reply_text("⚠️ Tez orada ushbu bo‘lim tayyor bo‘ladi!")
        return

    admin_list_text = "\n".join([f"👤 @{u}" for u in admins])

    text = (
        "📞 *Administratorlar bilan bog‘lanish*\n\n"
        "https://t.me/+4boksuF1saczMjI6\n\n"
        "✉️ Ushbu guruhga xabaringizni yo‘llang va tez orada javob olasiz."
    )

    await update.message.reply_text(text, parse_mode="Markdown")
