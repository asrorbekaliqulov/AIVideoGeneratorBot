import sqlite3
import os

DB_NAME = os.getenv("DB_NAME", "app.db")


# =====================================================
#  CREATE
# =====================================================
def create_channel(channel_id, name=None, type=None, url=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    try:
        c.execute("""
            INSERT INTO channel (channel_id, name, type, url)
            VALUES (?, ?, ?, ?)
        """, (channel_id, name, type, url))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # channel_id UNIQUE bo‘lgani uchun

    conn.close()


# =====================================================
#  READ
# =====================================================
def get_channel(channel_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT * FROM channel WHERE channel_id = ?", (channel_id,))
    result = c.fetchone()

    conn.close()
    return result


def get_all_channels():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT * FROM channel")
    result = c.fetchall()

    conn.close()
    return result


# =====================================================
#  UPDATE
# =====================================================
def update_channel(channel_id, **kwargs):
    if not kwargs:
        return False

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    fields = ", ".join([f"{key}=?" for key in kwargs])
    values = list(kwargs.values())

    query = f"UPDATE channel SET {fields} WHERE channel_id=?"
    c.execute(query, values + [channel_id])

    conn.commit()
    conn.close()
    return True


# =====================================================
#  DELETE
# =====================================================
def delete_channel(channel_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("DELETE FROM channel WHERE channel_id=?", (channel_id,))
    conn.commit()
    conn.close()


# =====================================================
#  FLEXIBLE FILTER
# =====================================================
def filter_channels(**kwargs):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    conditions = []
    values = []

    for key, value in kwargs.items():
        conditions.append(f"{key}=?")
        values.append(value)

    query = "SELECT * FROM channel"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    c.execute(query, values)
    rows = c.fetchall()

    conn.close()
    return rows
