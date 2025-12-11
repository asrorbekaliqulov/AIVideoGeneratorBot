import sqlite3
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
import os
from math import ceil

DB_NAME = os.getenv("DB_NAME", "app.db")


async def get_home_keyboard():
    """
    Dynamic home keyboard:
    - Agar order mavjud bo'lsa, yuqorida order tugmalari, pastda murojaat va generatsiya sotib olish
    - Agar order yo'q bo'lsa, faqat murojaat tugmasi
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # faqat aktiv orderlarni olish
    c.execute("SELECT name FROM order_type WHERE is_active=1 ORDER BY created_at ASC")
    orders = [row[0] for row in c.fetchall()]
    conn.close()

    keyboard = []

    if orders:
        # yuqoriga order tugmalari
        buttons_per_row = ceil(len(orders) / 2)
        for i in range(0, len(orders), buttons_per_row):
            row = [KeyboardButton(text=name) for name in orders[i:i + buttons_per_row]]
            keyboard.append(row)

        # pastga doimiy tugmalar
        keyboard.append([
            KeyboardButton(text="🪄 Generatsiyalarni sotib olish"),
            KeyboardButton(text="📞 Murojaat")
        ])
    else:
        # order yo'q bo'lsa faqat murojaat
        keyboard.append([KeyboardButton(text="📞 Murojaat")])

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)



BACK_BUTTON = "🔙 Orqaga"
CANCEL_BUTTON = "❌ Bekor qilish"

def get_back_cancel_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton(BACK_BUTTON), KeyboardButton(CANCEL_BUTTON)]],
        resize_keyboard=True
    )

def admin_panel_keyboard():
    keyboard = [
            [
                # InlineKeyboardButton("📢 Xabar yuborish", callback_data="broadcast"),
                InlineKeyboardButton("📊 Statistika", callback_data="statistics")
            ],
            [
                InlineKeyboardButton("📋 Zakaz turi", callback_data="order_type"),
                # InlineKeyboardButton("💰 Payment", callback_data="payment")
            ],
            [
            #     InlineKeyboardButton("👤 User boshqaruvi", callback_data="user_management"),
                InlineKeyboardButton("🛡 Admin boshqaruvi", callback_data="admin_management")
            ],
            # [InlineKeyboardButton("💾 Export", callback_data="export")]
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup

def admin_action_buttons(order_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎥 Qabul qilish", callback_data=f"take:{order_id}"),
            InlineKeyboardButton("❌ Bekor qilish", callback_data=f"cancel:{order_id}")
        ]
    ])


def skip_button(order_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➡️ O‘tkazib yuborish", callback_data=f"skip:{order_id}")]
    ])


def refund_buttons(order_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Ha", callback_data=f"refund_yes:{order_id}"),
            InlineKeyboardButton("Yo‘q", callback_data=f"refund_no:{order_id}")
        ]
    ])

def admin_control_buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Adminlar ro'yxati", callback_data="list_admins")
        ],
        [
            InlineKeyboardButton("Admin qo'shish", callback_data="add_admin"),
            InlineKeyboardButton("Admin o'chirish", callback_data="remove_admin")
        ],
        [
            InlineKeyboardButton("Orqaga", callback_data="admin_panel")
        ]
    ])