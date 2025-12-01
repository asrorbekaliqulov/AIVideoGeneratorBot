import sqlite3
from datetime import datetime
import os

DB_NAME = os.getenv("DB_NAME", "app.db")


# =====================================================
#  CREATE
# =====================================================

def create_video_order(user_id, order_type_id, image_file_id, amount=15000):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    now = datetime.utcnow().isoformat()

    c.execute("""
        INSERT INTO video_order (user_id, order_type_id, image_file_id, status, amount, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, order_type_id, image_file_id, "waiting", amount, now))

    conn.commit()
    conn.close()


# =====================================================
#  READ
# =====================================================

def get_video_order(order_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT * FROM video_order WHERE id=?", (order_id,))
    row = c.fetchone()

    conn.close()
    return row


def get_user_video_orders(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT * FROM video_order WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    rows = c.fetchall()

    conn.close()
    return rows


def get_waiting_orders():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT * FROM video_order WHERE status='waiting' ORDER BY created_at ASC")
    rows = c.fetchall()

    conn.close()
    return rows


def get_finished_orders():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT * FROM video_order WHERE status='done'")
    rows = c.fetchall()

    conn.close()
    return rows


# =====================================================
#  UPDATE
# =====================================================

def update_video_order(order_id, **kwargs):
    if not kwargs:
        return False

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    fields = ", ".join([f"{key}=?" for key in kwargs])
    values = list(kwargs.values())

    query = f"UPDATE video_order SET {fields} WHERE id=?"
    c.execute(query, values + [order_id])

    conn.commit()
    conn.close()
    return True


def set_order_status(order_id, status, video_file_id=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    now = datetime.utcnow().isoformat()

    if status == "done":
        c.execute("""
            UPDATE video_order
            SET status=?, video_file_id=?, finished_at=?
            WHERE id=?
        """, (status, video_file_id, now, order_id))

    else:
        c.execute("""
            UPDATE video_order
            SET status=?
            WHERE id=?
        """, (status, order_id))

    conn.commit()
    conn.close()


def cancel_order(order_id, reason):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    now = datetime.utcnow().isoformat()

    c.execute("""
        UPDATE video_order
        SET status='canceled', cancel_reason=?, finished_at=?
        WHERE id=?
    """, (reason, now, order_id))

    conn.commit()
    conn.close()


# =====================================================
#  DELETE
# =====================================================

def delete_video_order(order_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("DELETE FROM video_order WHERE id=?", (order_id,))
    conn.commit()
    conn.close()


# =====================================================
#  FILTERS
# =====================================================

def filter_video_orders(**kwargs):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    conditions = []
    values = []

    for key, value in kwargs.items():
        conditions.append(f"{key}=?")
        values.append(value)

    query = "SELECT * FROM video_order"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    c.execute(query, values)
    rows = c.fetchall()

    conn.close()
    return rows


# =====================================================
#  ANALYTICS / STATS
# =====================================================

def get_total_orders():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM video_order")
    total = c.fetchone()[0]

    conn.close()
    return total


def get_total_revenue():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT SUM(amount) FROM video_order WHERE status='done'")
    total = c.fetchone()[0]

    conn.close()
    return total or 0


def top_users_by_orders(limit=10):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        SELECT user_id, COUNT(*) AS order_count
        FROM video_order
        GROUP BY user_id
        ORDER BY order_count DESC
        LIMIT ?
    """, (limit,))

    rows = c.fetchall()
    conn.close()
    return rows


def top_users_by_spent(limit=10):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        SELECT user_id, SUM(amount) AS total_spent
        FROM video_order
        WHERE status='done'
        GROUP BY user_id
        ORDER BY total_spent DESC
        LIMIT ?
    """, (limit,))

    rows = c.fetchall()
    conn.close()
    return rows

import sqlite3
import os
from datetime import datetime
from types import SimpleNamespace

DB_NAME = os.getenv("DB_NAME", "app.db")


# ---------------------------------------------
# TELEGRAM USERNI OLISH
# ---------------------------------------------
def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, user_id, first_name, username, balance FROM telegram_user WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return None

    return SimpleNamespace(
        id=row[0],
        user_id=row[1],
        first_name=row[2],
        username=row[3],
        balance=row[4]
    )


# ---------------------------------------------
# VIDEO ORDERNI OLISH
# ---------------------------------------------
# def get_video_order(order_id):
#     conn = sqlite3.connect(DB_NAME)
#     c = conn.cursor()
#     c.execute("""
#         SELECT vo.id, vo.user_id, vo.order_type_id, vo.image_file_id,
#                vo.video_file_id, vo.status, vo.amount,
#                u.user_id, u.username
#         FROM video_order vo
#         JOIN telegram_user u ON vo.user_id = u.id
#         WHERE vo.id=?
#     """, (order_id,))
#     row = c.fetchone()
#     conn.close()

#     if not row:
#         return None

#     user = SimpleNamespace(id=row[1], user_id=row[7], username=row[8])

#     return SimpleNamespace(
#         id=row[0],
#         user=user,
#         order_type_id=row[2],
#         image_file_id=row[3],
#         video_file_id=row[4],
#         status=row[5],
#         amount=row[6]
#     )


# ---------------------------------------------
# VIDEO FILE ID YANGILASH
# ---------------------------------------------
def update_video_order_video_file(order_id, file_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "UPDATE video_order SET video_file_id=?, status='ready' WHERE id=?",
        (file_id, order_id)
    )
    conn.commit()
    conn.close()


# ---------------------------------------------
# ORDER STATUS YANGILASH + reason
# ---------------------------------------------
def update_video_order_status(order_id, status, reason=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "UPDATE video_order SET status=?, cancel_reason=?, finished_at=? WHERE id=?",
        (status, reason, datetime.now().isoformat(), order_id)
    )
    conn.commit()
    conn.close()
