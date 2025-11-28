# core/db.py
import sqlite3
import os
from .config import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()

    # ⚠️ DEV-ONLY: drop the old table if it exists, so schema is always up to date
    cur.execute("DROP TABLE IF EXISTS listings")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    conn.close()
