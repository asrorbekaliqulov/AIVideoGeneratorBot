import sqlite3
import os
from datetime import datetime

DB_NAME = os.getenv("DB_NAME", "app.db")


def create_payment(user_id, amount, status="pending", cheque_id=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.utcnow().isoformat()

    c.execute("""
        INSERT INTO payment (user_id, amount, status, created_at, cheque_id)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, amount, status, now, cheque_id))

    conn.commit()
    conn.close()


def get_payment(payment_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT * FROM payment WHERE id=?", (payment_id,))
    data = c.fetchone()

    conn.close()
    return data

def get_all_payments():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT * FROM payment ORDER BY id DESC")
    rows = c.fetchall()

    conn.close()
    return rows


def update_payment(payment_id, **kwargs):
    if not kwargs:
        return False

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    fields = []
    values = []

    for key, val in kwargs.items():
        fields.append(f"{key}=?")
        values.append(val)

    # agar status "confirmed" bo'lsa confirmed_at saqlanadi
    if "status" in kwargs and kwargs["status"] == "confirmed":
        fields.append("confirmed_at=?")
        values.append(datetime.utcnow().isoformat())

    query = f"UPDATE payment SET {', '.join(fields)} WHERE id=?"

    c.execute(query, values + [payment_id])
    conn.commit()
    conn.close()
    return True


def delete_payment(payment_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("DELETE FROM payment WHERE id=?", (payment_id,))
    conn.commit()
    conn.close()

def filter_payments(**kwargs):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    conditions = []
    values = []

    for key, value in kwargs.items():
        conditions.append(f"{key}=?")
        values.append(value)

    query = "SELECT * FROM payment"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY id DESC"

    c.execute(query, values)
    rows = c.fetchall()

    conn.close()
    return rows

def get_total_payments_by_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        SELECT SUM(amount) FROM payment
        WHERE user_id=? AND status='confirmed'
    """, (user_id,))
    total = c.fetchone()[0] or 0

    conn.close()
    return total

def get_top_payers(limit=10):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        SELECT user_id, SUM(amount) as total_amount
        FROM payment
        WHERE status='confirmed'
        GROUP BY user_id
        ORDER BY total_amount DESC
        LIMIT ?
    """, (limit,))

    result = c.fetchall()
    conn.close()
    return result

def get_today_payments():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    today = datetime.utcnow().date().isoformat()

    c.execute("""
        SELECT * FROM payment
        WHERE created_at LIKE ?
    """, (today + "%",))

    rows = c.fetchall()
    conn.close()
    return rows

def count_successful_payments():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM payment WHERE status='confirmed'")
    total = c.fetchone()[0]

    conn.close()
    return total

def update_payment(payment_id, **kwargs):
    if not kwargs:
        return False

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # avval eski payment yozuvini olish
    c.execute("SELECT user_id, amount, status FROM payment WHERE id=?", (payment_id,))
    old = c.fetchone()

    if not old:
        conn.close()
        return False

    old_user_id, old_amount, old_status = old

    fields = []
    values = []

    for key, val in kwargs.items():
        fields.append(f"{key}=?")
        values.append(val)

    # STATUS CONFIRMED bo‘lsa confirmed_at ham qo‘shamiz
    adding_confirmed_at = False
    if "status" in kwargs and kwargs["status"] == "confirmed":
        fields.append("confirmed_at=?")
        values.append(datetime.utcnow().isoformat())
        adding_confirmed_at = True

    # UPDATE query
    query = f"UPDATE payment SET {', '.join(fields)} WHERE id=?"
    c.execute(query, values + [payment_id])
    conn.commit()

    # ================================
    #  TELEGRAM_USER.BALANCE AUT UPDATE
    # ================================
    if "status" in kwargs:

        # eski status pending bo‘lsa va yangi confirmed bo‘lsa → balans qo‘shiladi
        if old_status != "confirmed" and kwargs["status"] == "confirmed":
            c.execute("""
                UPDATE telegram_user 
                SET balance = balance + ?
                WHERE id=?
            """, (old_amount, old_user_id))
            conn.commit()

        # agar ilgarigi confirmed bo‘lsa va yangisi cancelled → balansdan ayiramiz
        if old_status == "confirmed" and kwargs["status"] != "confirmed":
            c.execute("""
                UPDATE telegram_user 
                SET balance = balance - ?
                WHERE id=?
            """, (old_amount, old_user_id))
            conn.commit()

    conn.close()
    return True

def get_payment_by_cheque_id(cheque_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT * FROM payment WHERE cheque_id=?", (cheque_id,))
    data = c.fetchone()

    conn.close()
    return data

def confirm_payment_by_cheque(cheque_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # paymentni olish
    c.execute("SELECT id FROM payment WHERE cheque_id=?", (cheque_id,))
    row = c.fetchone()

    if not row:
        conn.close()
        return False

    payment_id = row[0]
    conn.close()

    # statusni confirmed qilib qo‘yamiz
    return update_payment(payment_id, status="confirmed")
