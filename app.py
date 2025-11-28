import os
import random
import string
import sqlite3
import hashlib
from datetime import datetime
from typing import Optional, Set, Tuple

import streamlit as st

DB_PATH = "circle.db"

# ---------------------------
# Database helpers
# ---------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Users
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Connections (undirected graph by storing two directed edges)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS connections (
            user_id INTEGER NOT NULL,
            friend_id INTEGER NOT NULL,
            UNIQUE(user_id, friend_id)
        )
    """)

    # Invite codes
    cur.execute("""
        CREATE TABLE IF NOT EXISTS invite_codes (
            code TEXT PRIMARY KEY,
            inviter_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            used_by INTEGER
        )
    """)

    # Listings (now includes image_path)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            brand TEXT,
            condition TEXT,
            price REAL NOT NULL,
            currency TEXT NOT NULL DEFAULT 'USD',
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            image_path TEXT
        )
    """)

    conn.commit()
    conn.close()

# ---------------------------
# Auth helpers
# ---------------------------

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def create_user(
    name: str,
    email: str,
    password: str,
    invite_code: Optional[str] = None
):
    conn = get_db()
    cur = conn.cursor()

    password_hash = hash_password(password)
    now = datetime.utcnow().isoformat()

    try:
        cur.execute(
            "INSERT INTO users (email, name, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (email.lower().strip(), name.strip(), password_hash, now),
        )
        user_id = cur.lastrowid

        # If invite code provided and valid, connect inviter and new user
        if invite_code:
            cur.execute(
                "SELECT inviter_id, used_by FROM invite_codes WHERE code = ?",
                (invite_code.strip(),),
            )
            row = cur.fetchone()
            if row and row["used_by"] is None:
                inviter_id = row["inviter_id"]

                # Make connections both ways (undirected graph)
                cur.execute(
                    "INSERT OR IGNORE INTO connections (user_id, friend_id) VALUES (?, ?)",
                    (inviter_id, user_id),
                )
                cur.execute(
                    "INSERT OR IGNORE INTO connections (user_id, friend_id) VALUES (?, ?)",
                    (user_id, inviter_id),
                )

                # Mark invite as used
                cur.execute(
                    "UPDATE invite_codes SET used_by = ? WHERE code = ?",
                    (user_id, invite_code.strip()),
                )

        conn.commit()
        return user_id, None

    except sqlite3.IntegrityError:
        return None, "Email already registered."
    finally:
        conn.close()

def authenticate_user(email: str, password: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE email = ?",
        (email.lower().strip(),),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return None, "User not found."

    if hash_password(password) != row["password_hash"]:
        return None, "Incorrect password."

    return row, None

def get_user_by_id(user_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row

# ---------------------------
# Social graph helpers
# ---------------------------

def get_friends(user_id: int) -> Set[int]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT friend_id FROM connections WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return {row["friend_id"] for row in rows}

def can_trade(buyer_id: int, seller_id: int) -> Tuple[bool, Optional[str]]:
    """
    Return (allowed, relation_type)
    relation_type in {"self", "direct", "second_degree", None}
    """
    if buyer_id == seller_id:
        return True, "self"

    friends = get_friends(buyer_id)
    if seller_id in friends:
        return True, "direct"

    # Second-degree check
    for f in friends:
        f_friends = get_friends(f)
        if seller_id in f_friends:
            return True, "second_degree"

    return False, None

# ---------------------------
# Listings helpers
# ---------------------------

def create_listing(
    seller_id: int,
    title: str,
    description: str,
    category: str,
    brand: str,
    condition: str,
    price: float,
    currency: str = "USD",
    image_path: Optional[str] = None,
):
    conn = get_db()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute(
        """
        INSERT INTO listings (
            seller_id, title, description, category, brand, conditio_
