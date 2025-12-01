# sqlite_models_and_crud.py
# Auto-generated SQLite schema + CRUD helpers for the Django-like models.
# Note: This is a simplified version for SQLite and does NOT replicate all Django behavior.

import sqlite3
from datetime import datetime
import os

# Load environment variables
DB_NAME = os.getenv("DB_NAME", "app.db")

# -----------------------------
# Database initialization
# -----------------------------

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # TelegramUser
    c.execute('''CREATE TABLE IF NOT EXISTS telegram_user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        first_name TEXT,
        username TEXT,
        date_joined TEXT,
        last_active TEXT,
        is_admin INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        balance INTEGER DEFAULT 0
    );''')

    # Channel
    c.execute('''CREATE TABLE IF NOT EXISTS channel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id TEXT UNIQUE,
        name TEXT,
        type TEXT,
        url TEXT
    )''')

    # Referral
    c.execute('''CREATE TABLE IF NOT EXISTS referral (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referrer_id INTEGER,
        referred_user_id INTEGER,
        created_at TEXT,
        referral_price REAL DEFAULT 0.0,
        FOREIGN KEY(referrer_id) REFERENCES telegram_user(id),
        FOREIGN KEY(referred_user_id) REFERENCES telegram_user(id)
    )''')

    # Guide
    c.execute('''CREATE TABLE IF NOT EXISTS guide (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        status INTEGER DEFAULT 1,
        created_at TEXT,
        updated_at TEXT
    )''')

    # Appeal
    c.execute('''CREATE TABLE IF NOT EXISTS appeal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        admin_id INTEGER,
        message_id INTEGER,
        message TEXT,
        status INTEGER DEFAULT 0,
        created_at TEXT,
        FOREIGN KEY(user_id) REFERENCES telegram_user(id),
        FOREIGN KEY(admin_id) REFERENCES telegram_user(id)
    )''')

    # Payment
    c.execute('''CREATE TABLE IF NOT EXISTS payment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount INTEGER,
        status TEXT,
        created_at TEXT,
        cheque_id TEXT,
        confirmed_at TEXT,
        FOREIGN KEY(user_id) REFERENCES telegram_user(id)
    )''')

    # OrderType
    c.execute('''CREATE TABLE IF NOT EXISTS order_type (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        slug TEXT UNIQUE,
        price INTEGER,
        description TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TEXT,
        updated_at TEXT
    )''')

    # VideoOrder
    c.execute('''CREATE TABLE IF NOT EXISTS video_order (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        order_type_id INTEGER,
        image_file_id TEXT,
        video_file_id TEXT,
        status TEXT,
        amount INTEGER,
        created_at TEXT,
        finished_at TEXT,
        cancel_reason TEXT,
        FOREIGN KEY(user_id) REFERENCES telegram_user(id),
        FOREIGN KEY(order_type_id) REFERENCES order_type(id)
    )''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")