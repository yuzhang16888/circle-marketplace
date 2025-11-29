# backend/db.py
import os
import psycopg2
import psycopg2.extras

# We'll read the connection string from an environment variable
DB_URL = os.environ.get("SUPABASE_DB_URL")

if not DB_URL:
    raise RuntimeError(
        "SUPABASE_DB_URL is not set. "
        "Set it to your Supabase Postgres connection string."
    )


def get_connection():
    """
    Open a new database connection.
    Uses a dict-like cursor so rows come back as dicts.
    """
    conn = psycopg2.connect(
        DB_URL,
        cursor_factory=psycopg2.extras.RealDictCursor,
    )
    return conn


def get_users_count() -> int:
    """
    Simple test query: how many users are in the users table?
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM public.users;")
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row["count"]
