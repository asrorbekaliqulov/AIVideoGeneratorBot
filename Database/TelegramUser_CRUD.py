import sqlite3
from datetime import datetime
import os

DB_NAME = os.getenv("DB_NAME", "app.db")


# =====================================================
#  CRUD OPERATIONS
# =====================================================

def create_telegram_user(user_id, first_name=None, username=None, balance=0):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.utcnow().isoformat()

    try:
        c.execute("""
            INSERT INTO telegram_user (user_id, first_name, username, date_joined, last_active, balance)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, first_name, username, now, now, balance))
        conn.commit()
    except sqlite3.IntegrityError:
        pass

    conn.close()


def get_telegram_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT * FROM telegram_user WHERE user_id=?", (user_id,))
    result = c.fetchone()

    conn.close()
    return result

def get_user_balance(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT balance FROM telegram_user WHERE user_id=?", (user_id,))
    row = c.fetchone()

    conn.close()
    return row[0] if row else 0


def update_telegram_user(user_id, **kwargs):
    if not kwargs:
        return False
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    fields = ", ".join([f"{key}=?" for key in kwargs])
    values = list(kwargs.values())
    now = datetime.utcnow().isoformat()

    query = f"UPDATE telegram_user SET {fields}, last_active=? WHERE user_id=?"
    c.execute(query, values + [now, user_id])

    conn.commit()
    conn.close()

    return True


def delete_telegram_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("DELETE FROM telegram_user WHERE user_id=?", (user_id,))

    conn.commit()
    conn.close()


# =====================================================
#  ADMIN OPERATIONS
# =====================================================

def make_admin(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("UPDATE telegram_user SET is_admin=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


def remove_admin(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("UPDATE telegram_user SET is_admin=0 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


def get_admin_users(limit=3):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # username bo‘lgan adminlar
    c.execute("""
        SELECT username 
        FROM telegram_user
        WHERE is_admin = 1 AND username IS NOT NULL AND username != ''
        LIMIT ?
    """, (limit,))

    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_admin_count():
    """Bazadagi adminlar sonini qaytaradi"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM telegram_user WHERE is_admin=1")
    count = c.fetchone()[0]
    conn.close()
    return count

def is_user_admin(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT is_admin FROM telegram_user WHERE user_id=?", (user_id,))
    row = c.fetchone()

    conn.close()
    return row[0] == 1 if row else False

# =====================================================
#  STATISTICS
# =====================================================

def get_total_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM telegram_user")
    total = c.fetchone()[0]

    conn.close()
    return total


def get_active_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM telegram_user WHERE is_active=1")
    total = c.fetchone()[0]

    conn.close()
    return total


def get_new_users_by_date(date):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM telegram_user WHERE date_joined LIKE ?", (date + "%",))
    count = c.fetchone()[0]

    conn.close()
    return count


# =====================================================
#  FLEXIBLE FILTER
# =====================================================

def filter_users(**kwargs):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    conditions = []
    values = []

    for key, value in kwargs.items():
        conditions.append(f"{key}=?")
        values.append(value)

    query = "SELECT * FROM telegram_user"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    c.execute(query, values)
    rows = c.fetchall()

    conn.close()
    return rows

def get_all_user_ids():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT user_id FROM telegram_user")
    ids = [row[0] for row in c.fetchall()]

    conn.close()
    return ids
