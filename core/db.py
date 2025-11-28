# core/db.py
import sqlite3
import os
from .config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # DEV MODE: recreate everything so we start fresh
    cur.execute("DROP TABLE IF EXISTS friendships")
    cur.execute("DROP TABLE IF EXISTS listings")
    cur.execute("DROP TABLE IF EXISTS users")

    cur.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            display_name TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cur.execute("""
        CREATE TABLE friendships (
            user_id INTEGER NOT NULL,
            friend_user_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, friend_user_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (friend_user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


def insert_user_if_not_exists(email, display_name=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    if row:
        conn.close()
        return row["id"]

    cur.execute(
        "INSERT INTO users (email, display_name) VALUES (?, ?)",
        (email, display_name or email.split("@")[0]),
    )
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    return user_id


def insert_listing(user_id, title, description, price, image_path=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO listings (user_id, title, description, price, image_path)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, title, description, price, image_path),
    )
    conn.commit()
    listing_id = cur.lastrowid
    conn.close()
    return listing_id


def get_friend_ids(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT friend_user_id FROM friendships WHERE user_id = ?",
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [r["friend_user_id"] for r in rows]


def get_friend_listings(user_id):
    friend_ids = get_friend_ids(user_id)
    if not friend_ids:
        return []

    conn = get_connection()
    cur = conn.cursor()

    placeholders = ",".join("?" for _ in friend_ids)
    query = f"""
        SELECT l.id, l.title, l.description, l.price,
               l.image_path, l.created_at,
               u.display_name AS seller_name
        FROM listings l
        JOIN users u ON u.id = l.user_id
        WHERE l.user_id IN ({placeholders})
        ORDER BY l.created_at DESC
    """

    cur.execute(query, friend_ids)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_all_listings():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT l.id, l.title, l.description, l.price,
               l.image_path, l.created_at,
               u.display_name AS seller_name
        FROM listings l
        JOIN users u ON u.id = l.user_id
        ORDER BY l.created_at DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def add_friend(user_id, friend_user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO friendships (user_id, friend_user_id) VALUES (?, ?)",
        (user_id, friend_user_id),
    )
    conn.commit()
    conn.close()
