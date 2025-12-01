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
        f"{admin_list_text}\n\n"
        "✉️ Adminlarimizga xabaringizni yo‘llang yoki ularga murojaat qiling."
    )

    await update.message.reply_text(text, parse_mode="Markdown")
