# core/db.py
import sqlite3
import os
import secrets
from .config import DB_PATH


def get_connection():
    """Return a SQLite connection with Row dict-like access."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Initialize DB tables if they don't exist.
    We DO NOT drop tables here, so data persists across reruns.
    Also ensure new columns exist via ALTER TABLE calls.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Users table – full schema (CREATE IF NOT EXISTS won't add missing cols)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            display_name TEXT,
            first_name TEXT,
            last_name TEXT,
            phone TEXT,
            inviter_name TEXT,
            password_hash TEXT,
            profile_image_path TEXT
        )
        """
    )

    # Listings table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    # Friendships table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS friendships (
            user_id INTEGER NOT NULL,
            friend_user_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, friend_user_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (friend_user_id) REFERENCES users(id)
        )
        """
    )

    # Invites table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS invites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inviter_user_id INTEGER NOT NULL,
            code TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (inviter_user_id) REFERENCES users(id)
        )
        """
    )

    # ---- Schema upgrade for existing DBs: add missing columns on users ----
    for col, col_def in [
        ("first_name", "TEXT"),
        ("last_name", "TEXT"),
        ("phone", "TEXT"),
        ("inviter_name", "TEXT"),
        ("password_hash", "TEXT"),
        ("profile_image_path", "TEXT"),
    ]:
        try:
            cur.execute(f"ALTER TABLE users ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError:
            # Column already exists – ignore
            pass

    conn.commit()
    conn.close()


# ---------- USER HELPERS ----------

def get_user_by_email(email: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, email, display_name,
               first_name, last_name, phone,
               inviter_name, password_hash, profile_image_path
        FROM users
        WHERE email = ?
        """,
        (email,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def get_user_by_id(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, email, display_name,
               first_name, last_name, phone,
               inviter_name, password_hash, profile_image_path
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def create_user(email, password_hash, first_name, last_name, phone, inviter_name):
    """
    Create a new user with extended profile info.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Use first_name as display_name fallback, else email prefix
    base_display = first_name or email.split("@")[0]

    cur.execute(
        """
        INSERT INTO users (
            email, display_name,
            first_name, last_name, phone,
            inviter_name, password_hash
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            email,
            base_display,
            first_name,
            last_name,
            phone,
            inviter_name,
            password_hash,
        ),
    )
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    return user_id


def insert_user_if_not_exists(email, display_name=None):
    """
    Legacy helper – keep for compatibility with old code,
    but new auth flow uses create_user directly.
    """
    existing = get_user_by_email(email)
    if existing:
        return existing["id"]
    # Minimal create if somehow called
    return create_user(email, password_hash="", first_name=None, last_name=None, phone=None, inviter_name=None)


def get_all_users():
    """Return all users in the system."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, email, display_name,
               first_name, last_name, phone,
               inviter_name, profile_image_path
        FROM users
        ORDER BY id ASC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def update_user_display_name(user_id: int, display_name: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET display_name = ? WHERE id = ?",
        (display_name, user_id),
    )
    conn.commit()
    conn.close()


def update_user_profile_image(user_id: int, image_path: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET profile_image_path = ? WHERE id = ?",
        (image_path, user_id),
    )
    conn.commit()
    conn.close()


# ---------- LISTING HELPERS ----------

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


def get_listings_for_user(user_id):
    """Return all listings created by a specific user."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT l.id, l.title, l.description, l.price,
               l.image_path, l.created_at
        FROM listings l
        WHERE l.user_id = ?
        ORDER BY l.created_at DESC
        """,
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_all_listings():
    """Return all listings with seller display name."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT l.id, l.title, l.description, l.price,
               l.image_path, l.created_at,
               u.display_name AS seller_name
        FROM listings l
        JOIN users u ON u.id = l.user_id
        ORDER BY l.created_at DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


# ---------- FRIENDSHIP HELPERS ----------

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
    """Return listings only from the user's friends."""
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


def add_friend(user_id, friend_user_id):
    """Create a friendship link if it doesn’t exist yet."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR IGNORE INTO friendships (user_id, friend_user_id)
        VALUES (?, ?)
        """,
        (user_id, friend_user_id),
    )
    conn.commit()
    conn.close()


# ---------- INVITE HELPERS ----------

def create_invite_code(inviter_user_id: int) -> str:
    """Generate and store a new invite code for this user."""
    code = secrets.token_urlsafe(6)[:8]  # short, shareable
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO invites (inviter_user_id, code)
        VALUES (?, ?)
        """,
        (inviter_user_id, code),
    )
    conn.commit()
    conn.close()
    return code


def get_invite_codes_for_user(inviter_user_id: int):
    """Return all invite codes created by this user. Safe even if table is missing."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT code, created_at
            FROM invites
            WHERE inviter_user_id = ?
            ORDER BY created_at DESC
            """,
            (inviter_user_id,),
        )
        rows = cur.fetchall()
    except sqlite3.OperationalError as e:
        # If the invites table doesn't exist yet for some reason,
        # fail gracefully and just return no codes.
        if "no such table" in str(e).lower():
            rows = []
        else:
            raise
    finally:
        conn.close()
    return rows


def get_invite_by_code(code: str):
    """Return invite row for a given code, or None if invalid."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, inviter_user_id, code, created_at
        FROM invites
        WHERE code = ?
        """,
        (code,),
    )
    row = cur.fetchone()
    conn.close()
    return row
