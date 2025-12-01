import sqlite3
from datetime import datetime
import os
from slugify import slugify   # pip install python-slugify

DB_NAME = os.getenv("DB_NAME", "app.db")


# =====================================================
#  CREATE
# =====================================================

def create_order_type(name, price, description="", is_active=1):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    slug_value = slugify(name)
    now = datetime.utcnow().isoformat()

    try:
        c.execute("""
            INSERT INTO order_type (name, slug, price, description, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, slug_value, price, description, is_active, now, now))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # name yoki slug unique bo'lmasa xatoni yutamiz

    conn.close()


# =====================================================
#  READ
# =====================================================

def get_order_type(order_type_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT * FROM order_type WHERE id=?", (order_type_id,))
    row = c.fetchone()

    conn.close()
    return row


def get_order_type_by_slug(slug):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT * FROM order_type WHERE slug=?", (slug,))
    row = c.fetchone()

    conn.close()
    return row


def get_all_order_types(active_only=False):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    if active_only:
        c.execute("SELECT * FROM order_type WHERE is_active=1 ORDER BY created_at DESC")
    else:
        c.execute("SELECT * FROM order_type ORDER BY created_at DESC")

    rows = c.fetchall()
    conn.close()
    return rows


# =====================================================
#  UPDATE
# =====================================================

def update_order_type(order_type_id, **kwargs):
    if not kwargs:
        return False

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Agar name o'zgarsa slug ham o'zgaradi
    if "name" in kwargs:
        kwargs["slug"] = slugify(kwargs["name"])

    fields = ", ".join([f"{key}=?" for key in kwargs])
    values = list(kwargs.values())
    now = datetime.utcnow().isoformat()

    query = f"""
        UPDATE order_type
        SET {fields}, updated_at=?
        WHERE id=?
    """

    c.execute(query, values + [now, order_type_id])
    conn.commit()
    conn.close()
    return True


# =====================================================
#  DELETE
# =====================================================

def delete_order_type(order_type_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("DELETE FROM order_type WHERE id=?", (order_type_id,))
    conn.commit()

    conn.close()


# =====================================================
#  FILTER & SEARCH
# =====================================================

def filter_order_types(**kwargs):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    conditions = []
    values = []

    for key, value in kwargs.items():
        conditions.append(f"{key}=?")
        values.append(value)

    query = "SELECT * FROM order_type"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    c.execute(query, values)
    rows = c.fetchall()

    conn.close()
    return rows


# =====================================================
#  SORTING HELPERS
# =====================================================

def get_order_types_sorted_by_price(desc=False):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    if desc:
        c.execute("SELECT * FROM order_type ORDER BY price DESC")
    else:
        c.execute("SELECT * FROM order_type ORDER BY price ASC")

    rows = c.fetchall()
    conn.close()
    return rows
