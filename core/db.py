# core/db.py

import sqlite3
# import secrets
import json
import os

from .config import DB_PATH

# --- Optional SQLAlchemy setup (not required for current sqlite helpers, but kept for future use) ---
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite URL – keep it in project root as circle.db
DATABASE_URL = "sqlite:///./circle.db"

# Needed for SQLite + multiple threads (Streamlit)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Simple helper for future SQLAlchemy-based code.

    Current app mostly uses direct sqlite3 helpers below,
    but we keep this so existing imports don't break.
    """
    return SessionLocal()


# ----------------- Low-level sqlite3 connection helpers -----------------


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

    # ---------------- USERS ----------------
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
            profile_image_path TEXT,
            invited_by_user_id INTEGER,
            stripe_account_id TEXT,
            stripe_onboarded INTEGER DEFAULT 0,
            FOREIGN KEY (invited_by_user_id) REFERENCES users(id)
        )
        """
    )

    # ---------------- LISTINGS ----------------
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

    # ---------------- FRIENDSHIPS ----------------
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

    # ---------------- INVITES ----------------
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

    # ---------------- ORDERS ----------------
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_id INTEGER NOT NULL,
            seller_id INTEGER NOT NULL,
            listing_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            total_price REAL NOT NULL,
            shipping_name TEXT,
            shipping_address1 TEXT,
            shipping_address2 TEXT,
            shipping_city TEXT,
            shipping_state TEXT,
            shipping_postal_code TEXT,
            shipping_country TEXT,
            shipping_phone TEXT,
            payment_method TEXT,
            buyer_note TEXT,
            tracking_number TEXT,
            carrier TEXT,
            estimated_delivery_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (buyer_id) REFERENCES users(id),
            FOREIGN KEY (seller_id) REFERENCES users(id),
            FOREIGN KEY (listing_id) REFERENCES listings(id)
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
        ("invited_by_user_id", "INTEGER"),
        ("stripe_account_id", "TEXT"),
        ("stripe_onboarded", "INTEGER DEFAULT 0"),
    ]:
        try:
            cur.execute(f"ALTER TABLE users ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError:
            # column already exists or table just created
            pass

    # ---- Schema upgrade for existing DBs: add missing columns on listings ----
    for col, col_def in [
        ("brand", "TEXT"),
        ("category", "TEXT"),
        ("condition", "TEXT"),
        ("retail_price", "REAL"),
        ("image_paths", "TEXT"),
        ("status", "TEXT"),  # e.g. 'draft', 'published', 'inactive'
    ]:
        try:
            cur.execute(f"ALTER TABLE listings ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError:
            # column already exists or table just created
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
               inviter_name, password_hash, profile_image_path,
               invited_by_user_id,
               stripe_account_id, stripe_onboarded
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
               inviter_name, password_hash, profile_image_path,
               invited_by_user_id,
               stripe_account_id, stripe_onboarded
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def create_user(
    email,
    password_hash,
    first_name,
    last_name,
    phone,
    inviter_name,
    invited_by_user_id=None,
):
    """
    Create a new user with extended profile info.
    invited_by_user_id: the user_id of the inviter (if they signed up via invite).
    """
    conn = get_connection()
    cur = conn.cursor()

    base_display = first_name or email.split("@")[0]

    cur.execute(
        """
        INSERT INTO users (
            email, display_name,
            first_name, last_name, phone,
            inviter_name, password_hash, invited_by_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            email,
            base_display,
            first_name,
            last_name,
            phone,
            inviter_name,
            password_hash,
            invited_by_user_id,
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
    return create_user(
        email=email,
        password_hash="",
        first_name=None,
        last_name=None,
        phone=None,
        inviter_name=None,
        invited_by_user_id=None,
    )


def get_all_users():
    """Return all users in the system."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, email, display_name,
               first_name, last_name, phone,
               inviter_name, profile_image_path,
               invited_by_user_id,
               stripe_account_id, stripe_onboarded
        FROM users
        ORDER BY id ASC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_users_invited_by(inviter_user_id: int):
    """Return users who were invited by this user and successfully signed up."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            id,
            email,
            display_name,
            first_name,
            last_name,
            profile_image_path,
            stripe_account_id,
            stripe_onboarded
        FROM users
        WHERE invited_by_user_id = ?
        ORDER BY id ASC
        """,
        (inviter_user_id,),
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


def update_user_password_hash(user_id: int, password_hash: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (password_hash, user_id),
    )
    conn.commit()
    conn.close()


def update_user_stripe_account(
    user_id: int,
    stripe_account_id: str,
    onboarded: bool = False,
):
    """
    Save the Stripe Connect account ID for a user.
    onboarded=False for now; later we can flip it to True after verification.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE users
        SET stripe_account_id = ?, stripe_onboarded = ?
        WHERE id = ?
        """,
        (stripe_account_id, 1 if onboarded else 0, user_id),
    )
    conn.commit()
    conn.close()


# ---------- LISTING HELPERS ----------


def insert_listing(
    user_id,
    title,
    description,
    price,
    brand=None,
    category=None,
    condition=None,
    retail_price=None,
    image_paths=None,  # list of paths or None
    status="published",
):
    """
    Insert a new listing.

    image_paths: list of file paths (will be JSON-serialized).
    status: 'published', 'draft', or 'inactive'.
    """
    if image_paths:
        image_paths_json = json.dumps(image_paths)
        main_image_path = image_paths[0]
    else:
        image_paths_json = None
        main_image_path = None

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO listings (
            user_id, title, description, price,
            image_path, brand, category, condition,
            retail_price, image_paths, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            title,
            description,
            price,
            main_image_path,
            brand,
            category,
            condition,
            retail_price,
            image_paths_json,
            status,
        ),
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
        SELECT
            l.id,
            l.title,
            l.description,
            l.price,
            l.image_path,
            l.created_at,
            l.brand,
            l.category,
            l.condition,
            l.retail_price,
            l.image_paths,
            l.status
        FROM listings l
        WHERE l.user_id = ?
        ORDER BY l.created_at DESC
        """,
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows
def get_listing_by_id(listing_id: int):
    """Fetch a single listing with seller info."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            l.id,
            l.user_id,
            l.title,
            l.description,
            l.price,
            l.image_path,
            l.created_at,
            l.brand,
            l.category,
            l.condition,
            l.retail_price,
            l.image_paths,
            l.status,
            u.display_name AS seller_name
        FROM listings l
        JOIN users u ON u.id = l.user_id
        WHERE l.id = ?
        """,
        (listing_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def get_listings_by_ids(listing_ids):
    """
    Fetch listings (with seller name) for a given list of IDs.
    Returns [] if list is empty.
    """
    if not listing_ids:
        return []

    conn = get_connection()
    cur = conn.cursor()

    placeholders = ",".join("?" for _ in listing_ids)
    query = f"""
        SELECT
            l.id,
            l.user_id,
            l.title,
            l.description,
            l.price,
            l.image_path,
            l.created_at,
            l.brand,
            l.category,
            l.condition,
            l.retail_price,
            l.image_paths,
            l.status,
            u.display_name AS seller_name
        FROM listings l
        JOIN users u ON u.id = l.user_id
        WHERE l.id IN ({placeholders})
    """

    cur.execute(query, listing_ids)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_all_listings():
    """Return all *published* listings with seller display name."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            l.id,
            l.title,
            l.description,
            l.price,
            l.image_path,
            l.created_at,
            l.brand,
            l.category,
            l.condition,
            l.retail_price,
            l.image_paths,
            l.status,
            u.display_name AS seller_name
        FROM listings l
        JOIN users u ON u.id = l.user_id
        WHERE l.status IS NULL OR l.status = 'published'
        ORDER BY l.created_at DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def delete_listing(user_id: int, listing_id: int) -> bool:
    """Permanently delete a listing, only if it belongs to this user."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM listings WHERE id = ? AND user_id = ?",
        (listing_id, user_id),
    )
    deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def update_listing_status(user_id: int, listing_id: int, status: str) -> bool:
    """Update a listing status (draft/published/inactive), only if it belongs to this user."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE listings SET status = ? WHERE id = ? AND user_id = ?",
        (status, listing_id, user_id),
    )
    updated = cur.rowcount > 0
    conn.commit()
    conn.close()
    return updated


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
    """Return *published* listings only from the user's friends."""
    friend_ids = get_friend_ids(user_id)
    if not friend_ids:
        return []

    conn = get_connection()
    cur = conn.cursor()

    placeholders = ",".join("?" for _ in friend_ids)
    query = f"""
        SELECT
            l.id,
            l.title,
            l.description,
            l.price,
            l.image_path,
            l.created_at,
            l.brand,
            l.category,
            l.condition,
            l.retail_price,
            l.image_paths,
            l.status,
            u.display_name AS seller_name
        FROM listings l
        JOIN users u ON u.id = l.user_id
        WHERE l.user_id IN ({placeholders})
          AND (l.status IS NULL OR l.status = 'published')
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


# ---------- ORDER HELPERS ----------


def create_order(
    buyer_id: int,
    seller_id: int,
    listing_id: int,
    total_price: float,
    shipping_name: str,
    shipping_address1: str,
    shipping_address2: str,
    shipping_city: str,
    shipping_state: str,
    shipping_postal_code: str,
    shipping_country: str,
    shipping_phone: str,
    payment_method: str,
    buyer_note: str,
) -> int:
    """Create a new order record and return its ID."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO orders (
            buyer_id,
            seller_id,
            listing_id,
            status,
            total_price,
            shipping_name,
            shipping_address1,
            shipping_address2,
            shipping_city,
            shipping_state,
            shipping_postal_code,
            shipping_country,
            shipping_phone,
            payment_method,
            buyer_note
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            buyer_id,
            seller_id,
            listing_id,
            "pending",           # status
            total_price,
            shipping_name,
            shipping_address1,
            shipping_address2,
            shipping_city,
            shipping_state,
            shipping_postal_code,
            shipping_country,
            shipping_phone,
            payment_method,
            buyer_note,
        ),
    )

    conn.commit()
    order_id = cur.lastrowid
    conn.close()
    return order_id


def get_orders_for_buyer(buyer_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
        FROM orders
        WHERE buyer_id = ?
        ORDER BY created_at DESC
        """,
        (buyer_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_orders_for_seller(seller_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
        FROM orders
        WHERE seller_id = ?
        ORDER BY created_at DESC
        """,
        (seller_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def update_order_status(order_id: int, status: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE orders
        SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (status, order_id),
    )
    conn.commit()
    conn.close()

def update_order_stripe_info(
    order_id: int,
    stripe_session_id: str,
    stripe_payment_intent_id=None,
):
    """
    Attach Stripe checkout/payment info to an order.
    We fill payment_intent_id later on success.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE orders
        SET stripe_session_id = ?,
            stripe_payment_intent_id = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (stripe_session_id, stripe_payment_intent_id, order_id),
    )
    conn.commit()
    conn.close()

def update_order_shipping(
    order_id: int,
    tracking_number: str,
    carrier: str,
    estimated_delivery_date: str,
):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE orders
        SET tracking_number = ?,
            carrier = ?,
            estimated_delivery_date = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (tracking_number, carrier, estimated_delivery_date, order_id),
    )
    conn.commit()
    conn.close()


###########archive###############

# # core/db.py
# import sqlite3
# import os
# import secrets
# import json
# from .config import DB_PATH

# # core/db.py

# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base

# # SQLite URL – keep it in project root as circle.db
# DATABASE_URL = "sqlite:///./circle.db"

# # Needed for SQLite + multiple threads (Streamlit)
# engine = create_engine(
#     DATABASE_URL, connect_args={"check_same_thread": False}
# )

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = declarative_base()


# def get_db():
#     """
#     Simple helper for Streamlit to get a DB session.

#     Usage:
#         db = get_db()
#         db.query(User)...
#     Remember: this does NOT auto-close the session; for now that's OK for dev.
#     """
#     return SessionLocal()



# def get_connection():
#     """Return a SQLite connection with Row dict-like access."""
#     conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#     conn.row_factory = sqlite3.Row
#     return conn


# def init_db():
#     """
#     Initialize DB tables if they don't exist.
#     We DO NOT drop tables here, so data persists across reruns.
#     Also ensure new columns exist via ALTER TABLE calls.
#     """
#     conn = get_connection()
#     cur = conn.cursor()

#     # ---------------- USERS ----------------
#     cur.execute(
#         """
#         CREATE TABLE IF NOT EXISTS users (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             email TEXT UNIQUE NOT NULL,
#             display_name TEXT,
#             first_name TEXT,
#             last_name TEXT,
#             phone TEXT,
#             inviter_name TEXT,
#             password_hash TEXT,
#             profile_image_path TEXT,
#             invited_by_user_id INTEGER,
#             FOREIGN KEY (invited_by_user_id) REFERENCES users(id)
#         )
#         """
#     )

#     # ---------------- LISTINGS ----------------
#     cur.execute(
#         """
#         CREATE TABLE IF NOT EXISTS listings (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             user_id INTEGER NOT NULL,
#             title TEXT NOT NULL,
#             description TEXT NOT NULL,
#             price REAL NOT NULL,
#             image_path TEXT,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#             FOREIGN KEY (user_id) REFERENCES users(id)
#         )
#         """
#     )

#     # ---------------- FRIENDSHIPS ----------------
#     cur.execute(
#         """
#         CREATE TABLE IF NOT EXISTS friendships (
#             user_id INTEGER NOT NULL,
#             friend_user_id INTEGER NOT NULL,
#             PRIMARY KEY (user_id, friend_user_id),
#             FOREIGN KEY (user_id) REFERENCES users(id),
#             FOREIGN KEY (friend_user_id) REFERENCES users(id)
#         )
#         """
#     )

#     # ---------------- INVITES ----------------
#     cur.execute(
#         """
#         CREATE TABLE IF NOT EXISTS invites (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             inviter_user_id INTEGER NOT NULL,
#             code TEXT UNIQUE NOT NULL,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#             FOREIGN KEY (inviter_user_id) REFERENCES users(id)
#         )
#         """
#     )
#         # ---------------- ORDERS ----------------
#     cur.execute(
#         """
#         CREATE TABLE IF NOT EXISTS orders (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             buyer_id INTEGER NOT NULL,
#             seller_id INTEGER NOT NULL,
#             listing_id INTEGER NOT NULL,
#             status TEXT NOT NULL,
#             total_price REAL NOT NULL,
#             shipping_name TEXT,
#             shipping_address1 TEXT,
#             shipping_address2 TEXT,
#             shipping_city TEXT,
#             shipping_state TEXT,
#             shipping_postal_code TEXT,
#             shipping_country TEXT,
#             shipping_phone TEXT,
#             payment_method TEXT,
#             buyer_note TEXT,
#             tracking_number TEXT,
#             carrier TEXT,
#             estimated_delivery_date TEXT,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#             updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#             FOREIGN KEY (buyer_id) REFERENCES users(id),
#             FOREIGN KEY (seller_id) REFERENCES users(id),
#             FOREIGN KEY (listing_id) REFERENCES listings(id)
#         )
#         """
#     )


#     # ---- Schema upgrade for existing DBs: add missing columns on users ----
#     for col, col_def in [
#         ("first_name", "TEXT"),
#         ("last_name", "TEXT"),
#         ("phone", "TEXT"),
#         ("inviter_name", "TEXT"),
#         ("password_hash", "TEXT"),
#         ("profile_image_path", "TEXT"),
#         ("invited_by_user_id", "INTEGER"),
#     ]:
#         try:
#             cur.execute(f"ALTER TABLE users ADD COLUMN {col} {col_def}")
#         except sqlite3.OperationalError:
#             pass  # column already exists

#     # ---- Schema upgrade for existing DBs: add missing columns on listings ----
#     for col, col_def in [
#         ("brand", "TEXT"),
#         ("category", "TEXT"),
#         ("condition", "TEXT"),
#         ("retail_price", "REAL"),
#         ("image_paths", "TEXT"),
#         ("status", "TEXT"),  # e.g. 'draft', 'published', 'inactive'
#     ]:
#         try:
#             cur.execute(f"ALTER TABLE listings ADD COLUMN {col} {col_def}")
#         except sqlite3.OperationalError:
#        	    pass  # column already exists

#     conn.commit()
#     conn.close()


# # ---------- USER HELPERS ----------

# def get_user_by_email(email: str):
#     conn = get_connection()
#     cur = conn.cursor()
#     cur.execute(
#         """
#         SELECT id, email, display_name,
#                first_name, last_name, phone,
#                inviter_name, password_hash, profile_image_path,
#                invited_by_user_id
#         FROM users
#         WHERE email = ?
#         """,
#         (email,),
#     )
#     row = cur.fetchone()
#     conn.close()
#     return row


# def get_user_by_id(user_id: int):
#     conn = get_connection()
#     cur = conn.cursor()
#     cur.execute(
#         """
#         SELECT id, email, display_name,
#                first_name, last_name, phone,
#                inviter_name, password_hash, profile_image_path,
#                invited_by_user_id
#         FROM users
#         WHERE id = ?
#         """,
#         (user_id,),
#     )
#     row = cur.fetchone()
#     conn.close()
#     return row


# def create_user(email, password_hash, first_name, last_name, phone, inviter_name, invited_by_user_id=None):
#     """
#     Create a new user with extended profile info.
#     invited_by_user_id: the user_id of the inviter (if they signed up via invite).
#     """
#     conn = get_connection()
#     cur = conn.cursor()

#     base_display = first_name or email.split("@")[0]

#     cur.execute(
#         """
#         INSERT INTO users (
#             email, display_name,
#             first_name, last_name, phone,
#             inviter_name, password_hash, invited_by_user_id
#         )
#         VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#         """,
#         (
#             email,
#             base_display,
#             first_name,
#             last_name,
#             phone,
#             inviter_name,
#             password_hash,
#             invited_by_user_id,
#         ),
#     )
#     conn.commit()
#     user_id = cur.lastrowid
#     conn.close()
#     return user_id


# def insert_user_if_not_exists(email, display_name=None):
#     """
#     Legacy helper – keep for compatibility with old code,
#     but new auth flow uses create_user directly.
#     """
#     existing = get_user_by_email(email)
#     if existing:
#         return existing["id"]
#     return create_user(
#         email=email,
#         password_hash="",
#         first_name=None,
#         last_name=None,
#         phone=None,
#         inviter_name=None,
#         invited_by_user_id=None,
#     )


# def get_all_users():
#     """Return all users in the system."""
#     conn = get_connection()
#     cur = conn.cursor()
#     cur.execute(
#         """
#         SELECT id, email, display_name,
#                first_name, last_name, phone,
#                inviter_name, profile_image_path,
#                invited_by_user_id
#         FROM users
#         ORDER BY id ASC
#         """
#     )
#     rows = cur.fetchall()
#     conn.close()
#     return rows


# def get_users_invited_by(inviter_user_id: int):
#     """Return users who were invited by this user and successfully signed up."""
#     conn = get_connection()
#     cur = conn.cursor()
#     cur.execute(
#         """
#         SELECT
#             id,
#             email,
#             display_name,
#             first_name,
#             last_name,
#             profile_image_path
#         FROM users
#         WHERE invited_by_user_id = ?
#         ORDER BY id ASC
#         """,
#         (inviter_user_id,),
#     )
#     rows = cur.fetchall()
#     conn.close()
#     return rows


# def update_user_display_name(user_id: int, display_name: str):
#     conn = get_connection()
#     cur = conn.cursor()
#     cur.execute(
#         "UPDATE users SET display_name = ? WHERE id = ?",
#         (display_name, user_id),
#     )
#     conn.commit()
#     conn.close()


# def update_user_profile_image(user_id: int, image_path: str):
#     conn = get_connection()
#     cur = conn.cursor()
#     cur.execute(
#         "UPDATE users SET profile_image_path = ? WHERE id = ?",
#         (image_path, user_id),
#     )
#     conn.commit()
#     conn.close()


# def update_user_password_hash(user_id: int, password_hash: str):
#     conn = get_connection()
#     cur = conn.cursor()
#     cur.execute(
#         "UPDATE users SET password_hash = ? WHERE id = ?",
#         (password_hash, user_id),
#     )
#     conn.commit()
#     conn.close()


# # ---------- LISTING HELPERS ----------

# def insert_listing(
#     user_id,
#     title,
#     description,
#     price,
#     brand=None,
#     category=None,
#     condition=None,
#     retail_price=None,
#     image_paths=None,  # list of paths or None
#     status="published",
# ):
#     """
#     Insert a new listing.

#     image_paths: list of file paths (will be JSON-serialized).
#     status: 'published', 'draft', or 'inactive'.
#     """
#     if image_paths:
#         image_paths_json = json.dumps(image_paths)
#         main_image_path = image_paths[0]
#     else:
#         image_paths_json = None
#         main_image_path = None

#     conn = get_connection()
#     cur = conn.cursor()
#     cur.execute(
#         """
#         INSERT INTO listings (
#             user_id, title, description, price,
#             image_path, brand, category, condition,
#             retail_price, image_paths, status
#         )
#         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         """,
#         (
#             user_id,
#             title,
#             description,
#             price,
#             main_image_path,
#             brand,
#             category,
#             condition,
#             retail_price,
#             image_paths_json,
#             status,
#         ),
#     )
#     conn.commit()
#     listing_id = cur.lastrowid
#     conn.close()
#     return listing_id


# def get_listings_for_user(user_id):
#     """Return all listings created by a specific user."""
#     conn = get_connection()
#     cur = conn.cursor()
#     cur.execute(
#         """
#         SELECT
#             l.id,
#             l.title,
#             l.description,
#             l.price,
#             l.image_path,
#             l.created_at,
#             l.brand,
#             l.category,
#             l.condition,
#             l.retail_price,
#             l.image_paths,
#             l.status
#         FROM listings l
#         WHERE l.user_id = ?
#         ORDER BY l.created_at DESC
#         """,
#         (user_id,),
#     )
#     rows = cur.fetchall()
#     conn.close()
# def get_listings_by_ids(listing_ids):
#     """
#     Fetch listings (with seller name) for a given list of IDs.
#     Returns [] if list is empty.
#     """
#     if not listing_ids:
#         return []

#     conn = get_connection()
#     cur = conn.cursor()

#     placeholders = ",".join("?" for _ in listing_ids)
#     query = f"""
#         SELECT
#             l.id,
#             l.user_id,
#             l.title,
#             l.description,
#             l.price,
#             l.image_path,
#             l.created_at,
#             l.brand,
#             l.category,
#             l.condition,
#             l.retail_price,
#             l.image_paths,
#             l.status,
#             u.display_name AS seller_name
#         FROM listings l
#         JOIN users u ON u.id = l.user_id
#         WHERE l.id IN ({placeholders})
#     """

#     cur.execute(query, listing_ids)
#     rows = cur.fetchall()
#     conn.close()
#     return rows



# def get_all_listings():
#     """Return all *published* listings with seller display name."""
#     conn = get_connection()
#     cur = conn.cursor()
#     cur.execute(
#         """
#         SELECT
#             l.id,
#             l.title,
#             l.description,
#             l.price,
#             l.image_path,
#             l.created_at,
#             l.brand,
#             l.category,
#             l.condition,
#             l.retail_price,
#             l.image_paths,
#             l.status,
#             u.display_name AS seller_name
#         FROM listings l
#         JOIN users u ON u.id = l.user_id
#         WHERE l.status IS NULL OR l.status = 'published'
#         ORDER BY l.created_at DESC
#         """
#     )
#     rows = cur.fetchall()
#     conn.close()
#     return rows


# def delete_listing(user_id: int, listing_id: int) -> bool:
#     """Permanently delete a listing, only if it belongs to this user."""
#     conn = get_connection()
#     cur = conn.cursor()
#     cur.execute(
#         "DELETE FROM listings WHERE id = ? AND user_id = ?",
#         (listing_id, user_id),
#     )
#     deleted = cur.rowcount > 0
#     conn.commit()
#     conn.close()
#     return deleted


# def update_listing_status(user_id: int, listing_id: int, status: str) -> bool:
#     """Update a listing status (draft/published/inactive), only if it belongs to this user."""
#     conn = get_connection()
#     cur = conn.cursor()
#     cur.execute(
#         "UPDATE listings SET status = ? WHERE id = ? AND user_id = ?",
#         (status, listing_id, user_id),
#     )
#     updated = cur.rowcount > 0
#     conn.commit()
#     conn.close()
#     return updated


# # ---------- FRIENDSHIP HELPERS ----------

# def get_friend_ids(user_id):
#     conn = get_connection()
#     cur = conn.cursor()
#     cur.execute(
#         "SELECT friend_user_id FROM friendships WHERE user_id = ?",
#         (user_id,),
#     )
#     rows = cur.fetchall()
#     conn.close()
#     return [r["friend_user_id"] for r in rows]


# def get_friend_listings(user_id):
#     """Return *published* listings only from the user's friends."""
#     friend_ids = get_friend_ids(user_id)
#     if not friend_ids:
#         return []

#     conn = get_connection()
#     cur = conn.cursor()

#     placeholders = ",".join("?" for _ in friend_ids)
#     query = f"""
#         SELECT
#             l.id,
#             l.title,
#             l.description,
#             l.price,
#             l.image_path,
#             l.created_at,
#             l.brand,
#             l.category,
#             l.condition,
#             l.retail_price,
#             l.image_paths,
#             l.status,
#             u.display_name AS seller_name
#         FROM listings l
#         JOIN users u ON u.id = l.user_id
#         WHERE l.user_id IN ({placeholders})
#           AND (l.status IS NULL OR l.status = 'published')
#         ORDER BY l.created_at DESC
#     """

#     cur.execute(query, friend_ids)
#     rows = cur.fetchall()
#     conn.close()
#     return rows


# def add_friend(user_id, friend_user_id):
#     """Create a friendship link if it doesn’t exist yet."""
#     conn = get_connection()
#     cur = conn.cursor()
#     cur.execute(
#         """
#         INSERT OR IGNORE INTO friendships (user_id, friend_user_id)
#         VALUES (?, ?)
#         """,
#         (user_id, friend_user_id),
#     )
#     conn.commit()
#     conn.close()


# # ---------- INVITE HELPERS ----------

# def create_invite_code(inviter_user_id: int) -> str:
#     """Generate and store a new invite code for this user."""
#     code = secrets.token_urlsafe(6)[:8]  # short, shareable
#     conn = get_connection()
#     cur = conn.cursor()
#     cur.execute(
#         """
#         INSERT INTO invites (inviter_user_id, code)
#         VALUES (?, ?)
#         """,
#         (inviter_user_id, code),
#     )
#     conn.commit()
#     conn.close()
#     return code


# def get_invite_codes_for_user(inviter_user_id: int):
#     """Return all invite codes created by this user. Safe even if table is missing."""
#     conn = get_connection()
#     cur = conn.cursor()
#     try:
#         cur.execute(
#             """
#             SELECT code, created_at
#             FROM invites
#             WHERE inviter_user_id = ?
#             ORDER BY created_at DESC
#             """,
#             (inviter_user_id,),
#         )
#         rows = cur.fetchall()
#     except sqlite3.OperationalError as e:
#         if "no such table" in str(e).lower():
#             rows = []
#         else:
#             raise
#     finally:
#         conn.close()
#     return rows


# def get_invite_by_code(code: str):
#     """Return invite row for a given code, or None if invalid."""
#     conn = get_connection()
#     cur = conn.cursor()
#     cur.execute(
#         """
#         SELECT id, inviter_user_id, code, created_at
#         FROM invites
#         WHERE code = ?
#         """,
#         (code,),
#     )
#     row = cur.fetchone()
#     conn.close()
#     return row
# # ---------- ORDER HELPERS ----------

# def create_order(
#     buyer_id: int,
#     seller_id: int,
#     listing_id: int,
#     total_price: float,
#     shipping_name: str,
#     shipping_address1: str,
#     shipping_address2: str,
#     shipping_city: str,
#     shipping_state: str,
#     shipping_postal_code: str,
#     shipping_country: str,
#     shipping_phone: str,
#     payment_method: str,
#     buyer_note: str,
# ) -> int:
#     """Create a new order record and return its ID."""
#     conn = get_connection()
#     cur = conn.cursor()

#     cur.execute(
#         """
#         INSERT INTO orders (
#             buyer_id,
#             seller_id,
#             listing_id,
#             status,
#             total_price,
#             shipping_name,
#             shipping_address1,
#             shipping_address2,
#             shipping_city,
#             shipping_state,
#             shipping_postal_code,
#             shipping_country,
#             shipping_phone,
#             payment_method,
#             buyer_note
#         )
#         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         """,
#         (
#             buyer_id,
#             seller_id,
#             listing_id,
#             "pending",           # status
#             total_price,
#             shipping_name,
#             shipping_address1,
#             shipping_address2,
#             shipping_city,
#             shipping_state,
#             shipping_postal_code,
#             shipping_country,
#             shipping_phone,
#             payment_method,
#             buyer_note,
#         ),
#     )

#     conn.commit()
#     order_id = cur.lastrowid
#     conn.close()
#     return order_id



# def get_orders_for_buyer(buyer_id: int):
#     conn = get_connection()
#     cur = conn.cursor()
#     cur.execute(
#         """
#         SELECT *
#         FROM orders
#         WHERE buyer_id = ?
#         ORDER BY created_at DESC
#         """,
#         (buyer_id,),
#     )
#     rows = cur.fetchall()
#     conn.close()
#     return rows


# def get_orders_for_seller(seller_id: int):
#     conn = get_connection()
#     cur = conn.cursor()
#     cur.execute(
#         """
#         SELECT *
#         FROM orders
#         WHERE seller_id = ?
#         ORDER BY created_at DESC
#         """,
#         (seller_id,),
#     )
#     rows = cur.fetchall()
#     conn.close()
#     return rows


# def update_order_status(order_id: int, status: str):
#     conn = get_connection()
#     cur = conn.cursor()
#     cur.execute(
#         """
#         UPDATE orders
#         SET status = ?, updated_at = CURRENT_TIMESTAMP
#         WHERE id = ?
#         """,
#         (status, order_id),
#     )
#     conn.commit()
#     conn.close()


# def update_order_shipping(
#     order_id: int,
#     tracking_number: str,
#     carrier: str,
#     estimated_delivery_date: str,
# ):
#     conn = get_connection()
#     cur = conn.cursor()
#     cur.execute(
#         """
#         UPDATE orders
#         SET tracking_number = ?,
#             carrier = ?,
#             estimated_delivery_date = ?,
#             updated_at = CURRENT_TIMESTAMP
#         WHERE id = ?
#         """,
#         (tracking_number, carrier, estimated_delivery_date, order_id),
#     )
#     conn.commit()
#     conn.close()
