# backend/db.py
import sqlite3
from pathlib import Path

# Path to your existing SQLite database (circle.db in project root)
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "circle.db"


def get_connection():
    """
    Open a connection to the local SQLite DB.
    Rows will be dict-like (sqlite3.Row).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_users_count() -> int:
    """
    Simple test query: how many users in the users table?
    If the users table doesn't exist yet, create it and return 0.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Ensure users table exists (minimal schema for now)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            is_verified INTEGER NOT NULL DEFAULT 0,
            invited_by_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    # Now count rows
    cur.execute("SELECT COUNT(*) AS count FROM users;")
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row["count"]

import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(email: str, password: str, full_name: str | None):
    conn = get_connection()
    cur = conn.cursor()

    hashed = hash_password(password)

    cur.execute(
        """
        INSERT INTO users (email, password_hash, full_name, is_verified)
        VALUES (?, ?, ?, 1)
        """,
        (email, hashed, full_name),
    )
    conn.commit()
    uid = cur.lastrowid
    conn.close()
    return uid

def get_user_by_email(email: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()
    return row
