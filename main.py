from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import os
from AdminControl.admin_menu import admin_start,admin_callback, admin_control_menu
from AdminControl.Add_admin import Admin_Add, auto_admin, handle_new_admin_selection
from Commands.start_command import start
from UserControl.search_user import search_conv_handler, handle_user_orders
from UserControl.user_panel import user_management_panel
from Handlers.OrderType import zakaz_conv
from Handlers.statistika import get_stats
from Handlers.GetOrder import video_order_conv
from Handlers.CheckOrder import accept_order, admin_video_conv
from Handlers.Payment import price_handler, paid_handler, cancel_handler, send_price_button, menu_handler
from Handlers.Contact import contact_admins
from Database.init_db import init_db
from dotenv import load_dotenv
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)


load_dotenv()

# Bot Token
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN topilmadi! .env faylini tekshiring.")   

def main():
    # Application yaratishda persistence va job_queue parametrlarini qo'shamiz
    app = Application.builder().token(TOKEN).build()

    init_db()
    print("Database initialized successfully.")

        # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_start))
    app.add_handler(CommandHandler("admin0890", auto_admin))
    app.add_handler(zakaz_conv)
    app.add_handler(video_order_conv)
    app.add_handler(admin_video_conv)

    app.add_handler(send_price_button)
    app.add_handler(menu_handler)
    app.add_handler(price_handler)
    app.add_handler(paid_handler)
    app.add_handler(cancel_handler)
    app.add_handler(CallbackQueryHandler(get_stats, pattern="^statistics$"))
    app.add_handler(CallbackQueryHandler(start, pattern="^main_menu$"))
    app.add_handler(CallbackQueryHandler(admin_start, pattern="^admin_panel$"))
    app.add_handler(CallbackQueryHandler(accept_order, pattern="^order_accept:"))
    app.add_handler(CallbackQueryHandler(Admin_Add, pattern="^add_admin$"))
    app.add_handler(CallbackQueryHandler(admin_control_menu, pattern="^admin_management$"))
    app.add_handler(search_conv_handler)
    app.add_handler(CallbackQueryHandler(handle_user_orders, pattern="^userorders_"))
    app.add_handler(CallbackQueryHandler(user_management_panel, pattern="^user_management$"))
    app.add_handler(CallbackQueryHandler(admin_callback))

    app.add_handler(MessageHandler(filters.Regex("^📞 Murojaat$"), contact_admins))
    app.add_handler(MessageHandler(filters.Regex("^🔙 Orqаga$"), admin_start))

    app.add_handler(MessageHandler(filters.USER & ~filters.COMMAND, handle_new_admin_selection))


    print("The bot is running!!!")
    app.run_polling()

if __name__ == "__main__":
    main()