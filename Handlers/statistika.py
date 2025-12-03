import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import CallbackContext
from datetime import datetime
import os
import time

# Ilova ma'lumotlar bazasi nomi (sqlite_models_and_crud.py faylidan olingan)
DB_NAME = os.getenv("DB_NAME", "app.db")

# -----------------------------
# Ma'lumotlar bazasidan ma'lumot olish funksiyalari
# -----------------------------

def get_db_connection():
    """SQLite bilan ulanishni yaratadi va qaytaradi."""
    return sqlite3.connect(DB_NAME)

def get_all_users_for_check():
    """Faollikni tekshirish uchun barcha foydalanuvchilarning user_id'larini oladi."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT user_id, id FROM telegram_user")
    users = c.fetchall()
    conn.close()
    return users # [(user_id, db_id), ...]

def get_dashboard_stats():
    """Barcha statistik ma'lumotlarni DB dan oladi."""
    conn = get_db_connection()
    c = conn.cursor()

    # 1. Umumiy Foydalanuvchilar soni
    c.execute("SELECT COUNT(*) FROM telegram_user")
    total_users = c.fetchone()[0]

    # 2. To'lovlar (Payment) statistikasi
    c.execute("SELECT status, COUNT(*) FROM payment GROUP BY status")
    payment_stats_raw = dict(c.fetchall())
    total_payments = sum(payment_stats_raw.values())
    
    successful_payments = payment_stats_raw.get('successful', 0)
    cancelled_payments = payment_stats_raw.get('cancelled', 0)
    pending_payments = payment_stats_raw.get('pending', 0)

    # 3. Buyurtmalar (VideoOrder) statistikasi
    c.execute("SELECT status, COUNT(*) FROM video_order GROUP BY status")
    order_stats_raw = dict(c.fetchall())
    total_orders = sum(order_stats_raw.values())
    
    successful_orders = order_stats_raw.get('finished', 0) # 'finished' (muvaffaqiyatli tugallangan) deb faraz qilinadi
    cancelled_orders = order_stats_raw.get('cancelled', 0)
    pending_orders = order_stats_raw.get('pending', 0)

    # 4. Umumiy tushum (Muvaqqiyatli to'lovlar summasi)
    c.execute("SELECT SUM(amount) FROM payment WHERE status = 'successful'")
    total_revenue = c.fetchone()[0] or 0

    conn.close()

    return {
        'total_users': total_users,
        'payment': {
            'total': total_payments,
            'successful': successful_payments,
            'cancelled': cancelled_payments,
            'pending': pending_payments,
            'revenue': total_revenue
        },
        'order': {
            'total': total_orders,
            'successful': successful_orders,
            'cancelled': cancelled_orders,
            'pending': pending_orders
        }
    }

def update_user_activity_status(db_id, is_active):
    """Userning DB dagi is_active holatini yangilaydi."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE telegram_user SET is_active = ? WHERE id = ?", (is_active, db_id))
    conn.commit()
    conn.close()

# -----------------------------
# Telegram bot handler funksiyasi
# -----------------------------

async def get_stats(update: Update, context: CallbackContext) -> None:
    """
    Statistika ma'lumotlarini to'playdi, faollikni tekshiradi va xabarni yuboradi.
    """


    # Foydalanuvchiga kutish xabarini yuborish
    await update.callback_query.answer("📊 Statistika tayyorlanmoqda...")
    
    # Faol/Nofaol foydalanuvchilarni aniqlash
    all_users = get_all_users_for_check()
    active_users_count = 0
    inactive_users_count = 0
    
    # Har bir userga TYPING action yuborib faollikni tekshirish
    # Bu joyda API limitlarini hisobga oling! Kichik bazada sinab ko'rish tavsiya etiladi.
    for user_id, db_id in all_users:
        try:
            # ChatAction.TYPING yuborish
            await context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
            active_users_count += 1
            # Agar oldin nofaol bo'lib, endi javob bergan bo'lsa, DBni yangilash
            # update_user_activity_status(db_id, 1) # Kerak bo'lsa faollikni yangilaymiz
            time.sleep(0.05) # API limitini buzmaslik uchun ozgina kutish
        except Exception as e:
            # Agar bot bloklangan bo'lsa (yoki boshqa xatolik)
            inactive_users_count += 1
            # Foydalanuvchi botni bloklagan bo'lsa, DBda nofaol qilib belgilash
            update_user_activity_status(db_id, 0)

    # Boshqa statistik ma'lumotlarni olish
    stats = get_dashboard_stats()
    total_users_db = stats['total_users'] # DB dagi umumiy userlar soni

    # Xabar matnini shakllantirish (Har xil shriftlar va emojilar bilan)
    message_text = (
        "👑 <b>BOT STATISTIKASI</b> 📈\n"
        f"🗓 <i>Bugungi sana: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>\n"
        "\n"
        "<blockquote>--- 👤 <b>FOYDALANUVCHILAR</b> ---\n"
        f"<b>{total_users_db}</b> - Jami ro'yxatdan o'tgan userlar.\n"
        f"🟢 <b>{active_users_count}</b> - Faol (Hozirda botni bloklamaganlar).\n"
        f"🔴 <b>{inactive_users_count}</b> - Nofaol (Botni bloklaganlar).</blockquote>\n"
        "\n"
        "<blockquote>--- 💰 <b>TO'LOVLAR (PAYMENTS)</b> ---\n"
        f"💳 Jami tranzaksiyalar: <b>{stats['payment']['total']}</b> ta\n"
        f"✅ Muvaffaqiyatli: <b>{stats['payment']['successful']}</b> ta\n"
        f"⏳ Kutilayotgan: <b>{stats['payment']['pending']}</b> ta\n"
        f"❌ Bekor bo'lgan: <b>{stats['payment']['cancelled']}</b> ta\n"
        f"💵 Umumiy Tushum: <b>{stats['payment']['revenue']}</b> UZS</blockquote>\n"
        "\n"
        "<blockquote>--- 📦 <b>BUYURTMALAR (ORDERS)</b> ---\n"
        f"🗂 Jami Buyurtmalar: <b>{stats['order']['total']}</b> ta\n"
        f"✅ Muvaffaqiyatli: <b>{stats['order']['successful']}</b> ta\n"
        f"⏳ Kutilayotgan: <b>{stats['order']['pending']}</b> ta\n"
        f"❌ Bekor bo'lgan: <b>{stats['order']['cancelled']}</b> ta</blockquote>\n"
    )
    
    # Inline tugmalarni yaratish
    keyboard = [
        [
            InlineKeyboardButton("🔙 Admin Paneliga Qaytish", callback_data='admin_panel'),
            InlineKeyboardButton("🏠 User Paneliga Qaytish", callback_data='main_menu')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Kutish xabarini o'chirish va yangi statistikani yuborish
    await update.callback_query.edit_message_text(
        text = message_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

