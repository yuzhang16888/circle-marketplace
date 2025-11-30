# backend/db.py
import sqlite3
from pathlib import Path
from typing import Optional
import hashlib

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
from typing import Optional

def get_invites_by_inviter(invited_by_id: int):
    ensure_invites_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, email, invited_by_id, used_by_user_id, created_at, used_at
        FROM invites
        WHERE invited_by_id = %s
        ORDER BY created_at DESC
        """,
        (invited_by_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def ensure_users_table():
    """
    Make sure the users table exists.
    """
    conn = get_connection()
    cur = conn.cursor()
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
    conn.commit()
    conn.close()


def get_users_count() -> int:
    """
    Simple test query: how many users in the users table?
    """
    ensure_users_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM users;")
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row["count"]

def ensure_invites_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS invites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            invited_by_id INTEGER,
            used_by_user_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            used_at TEXT
        );
        """
    )
    conn.commit()
    conn.close()


def create_invite(email: str, invited_by_id: Optional[int] = None) -> int:
    ensure_invites_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO invites (email, invited_by_id)
        VALUES (?, ?)
        """,
        (email.lower().strip(), invited_by_id),
    )
    conn.commit()
    invite_id = cur.lastrowid
    conn.close()
    return invite_id


def get_invite_for_email(email: str):
    """
    Return an unused invite row for this email, or None.
    """
    ensure_invites_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM invites
        WHERE email = ? AND used_by_user_id IS NULL
        ORDER BY id DESC
        LIMIT 1
        """,
        (email.lower().strip(),),
    )
    row = cur.fetchone()
    conn.close()
    return row


def mark_invite_used(invite_id: int, user_id: int):
    ensure_invites_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE invites
        SET used_by_user_id = ?, used_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (user_id, invite_id),
    )
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    """
    Very simple password hash for now (SHA-256).
    """
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, stored_hash: str) -> bool:
    """
    Compare a plain-text password with a stored SHA-256 hash.
    """
    return hash_password(password) == stored_hash

def verify_password(password: str, stored_hash: str) -> bool:
    return hash_password(password) == stored_hash

def create_user(email: str, password: str, full_name: Optional[str] = None) -> int:
    """
    Insert a new user and return its id.
    """
    ensure_users_table()
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
    """
    Return a single user row by email, or None if not found.
    """
    ensure_users_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()
    return row
