import sqlite3
import os
from datetime import datetime

DB_NAME = os.getenv("DB_NAME", "app.db")


# =====================================================
#  CREATE (referral yozuvi yaratish)
# =====================================================
def create_referral(referrer_id, referred_user_id, referral_price=0.0):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.utcnow().isoformat()

    c.execute("""
        INSERT INTO referral (referrer_id, referred_user_id, created_at, referral_price)
        VALUES (?, ?, ?, ?)
    """, (referrer_id, referred_user_id, now, referral_price))

    conn.commit()
    conn.close()


def get_referral(referral_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT * FROM referral WHERE id=?", (referral_id,))
    result = c.fetchone()

    conn.close()
    return result


def get_all_referrals():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT * FROM referral ORDER BY id DESC")
    result = c.fetchall()

    conn.close()
    return result


def update_referral(referral_id, **kwargs):
    if not kwargs:
        return False

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    fields = ", ".join([f"{field}=?" for field in kwargs])
    values = list(kwargs.values())

    query = f"UPDATE referral SET {fields} WHERE id=?"
    c.execute(query, values + [referral_id])

    conn.commit()
    conn.close()
    return True


def delete_referral(referral_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("DELETE FROM referral WHERE id=?", (referral_id,))

    conn.commit()
    conn.close()


def filter_referrals(**kwargs):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    conditions = []
    values = []

    for key, value in kwargs.items():
        conditions.append(f"{key}=?")
        values.append(value)

    query = "SELECT * FROM referral"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    c.execute(query, values)
    rows = c.fetchall()

    conn.close()
    return rows
