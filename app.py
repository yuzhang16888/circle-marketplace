import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

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

    # Connections (undirected graph via 2 rows)
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

    # Listings
        # Listings
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

def create_user(name: str, email: str, password: str, invite_code: str | None = None):
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

                # Make connections both ways (undirected)
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

    except sqlite3.IntegrityError as e:
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

def get_friends(user_id: int) -> set[int]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT friend_id FROM connections WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return {row["friend_id"] for row in rows}

def can_trade(buyer_id: int, seller_id: int) -> tuple[bool, str | None]:
    """
    Return (allowed, relation_type)
    relation_type in {"self", "direct", "second_degree", None}
    """
    if buyer_id == seller_id:
        return True, "self"

    friends = get_friends(buyer_id)
    if seller_id in friends:
        return True, "direct"

    # Check second degree: is there a friend f where seller in friends_of_f?
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
):
    conn = get_db()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute(
        """
        INSERT INTO listings (
            seller_id, title, description, category, brand, condition,
            price, currency, status, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'available', ?)
        """,
        (
            seller_id,
            title.strip(),
            description.strip() if description else "",
            category.strip() if category else "",
            brand.strip() if brand else "",
            condition.strip() if condition else "",
            price,
            currency,
            now,
        ),
    )
    conn.commit()
    conn.close()

def get_all_listings():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT l.*, u.name as seller_name
        FROM listings l
        JOIN users u ON u.id = l.seller_id
        ORDER BY datetime(l.created_at) DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def get_my_listings(user_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT l.*, u.name as seller_name
        FROM listings l
        JOIN users u ON u.id = l.seller_id
        WHERE seller_id = ?
        ORDER BY datetime(l.created_at) DESC
        """,
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows

# ---------------------------
# Invite codes
# ---------------------------

import random
import string

def generate_invite_code(inviter_id: int) -> str:
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    conn = get_db()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute(
        "INSERT INTO invite_codes (code, inviter_id, created_at) VALUES (?, ?, ?)",
        (code, inviter_id, now),
    )
    conn.commit()
    conn.close()
    return code

def get_invite_codes_for_user(user_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM invite_codes WHERE inviter_id = ? ORDER BY datetime(created_at) DESC",
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows

# ---------------------------
# UI helpers
# ---------------------------

def require_login():
    if "user_id" not in st.session_state or st.session_state.user_id is None:
        st.warning("Please log in to use Circle Marketplace.")
        st.stop()

def show_auth_ui():
    tab_login, tab_signup = st.tabs(["Log in", "Sign up"])

    with tab_login:
        st.subheader("Log in")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Log in", use_container_width=True):
            if not email or not password:
                st.error("Please enter email and password.")
            else:
                user_row, err = authenticate_user(email, password)
                if err:
                    st.error(err)
                else:
                    st.session_state.user_id = user_row["id"]
                    st.session_state.user_name = user_row["name"]
                    st.session_state.user_email = user_row["email"]
                    st.success("Logged in!")
                    st.experimental_rerun()

    with tab_signup:
        st.subheader("Create an account")
        name = st.text_input("Name", key="signup_name")
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        invite_code = st.text_input(
            "Invite code (optional for now)", key="signup_invite_code"
        )

        if st.button("Sign up", use_container_width=True):
            if not name or not email or not password:
                st.error("Name, email and password are required.")
            else:
                user_id, err = create_user(name, email, password, invite_code or None)
                if err:
                    st.error(err)
                else:
                    st.session_state.user_id = user_id
                    st.session_state.user_name = name
                    st.session_state.user_email = email
                    st.success("Account created and logged in!")
                    st.experimental_rerun()

# ---------------------------
# Pages
# ---------------------------

def page_create_listing():
    require_login()
    st.subheader("Create a new listing")

    title = st.text_input("Title (e.g. 'Chanel Classic Flap Medium')")
    col1, col2 = st.columns(2)
    with col1:
        category = st.text_input("Category (e.g. 'Handbag', 'Card', 'Watch')")
        brand = st.text_input("Brand (optional)")
    with col2:
        condition = st.selectbox(
            "Condition",
            ["", "Brand new", "Like new", "Excellent", "Good", "Fair"],
            index=0,
        )
        price = st.number_input("Price (USD)", min_value=0.0, step=10.0)

    description = st.text_area("Description")

    if st.button("Publish listing", type="primary", use_container_width=True):
        if not title or price <= 0:
            st.error("Please provide at least a title and a positive price.")
        else:
            create_listing(
                seller_id=st.session_state.user_id,
                title=title,
                description=description,
                category=category,
                brand=brand,
                condition=condition,
                price=price,
            )
            st.success("Listing created!")
            st.experimental_rerun()

def page_browse_listings():
    require_login()
    st.subheader("Browse listings in your Circle")

    listings = get_all_listings()
    if not listings:
        st.info("No listings yet. Be the first to list something!")
        return

    for row in listings:
        seller_id = row["seller_id"]
        seller_name = row["seller_name"]
        allowed, relation = can_trade(st.session_state.user_id, seller_id)

        relation_label = ""
        if relation == "self":
            relation_label = "your own listing"
        elif relation == "direct":
            relation_label = "direct connection"
        elif relation == "second_degree":
            relation_label = "friend of a friend"

        box = st.container(border=True)
        with box:
            st.markdown(f"**{row['title']}**")
            meta_cols = st.columns(3)
            with meta_cols[0]:
                st.write(f"Seller: {seller_name}")
            with meta_cols[1]:
                st.write(f"Price: ${row['price']:,.2f} {row['currency']}")
            with meta_cols[2]:
                st.write(f"Status: {row['status']}")

            if row["category"]:
                st.caption(f"Category: {row['category']}")
            if row["brand"]:
                st.caption(f"Brand: {row['brand']}")
            if row["condition"]:
                st.caption(f"Condition: {row['condition']}")

            if row["description"]:
                st.write(row["description"])

            if allowed:
                st.success(f"You can trade with this seller ({relation_label}).")
                st.button(
                    "I'm interested (placeholder, no messaging yet)",
                    key=f"interest_{row['id']}",
                )
            else:
                st.warning(
                    "This seller is outside your 2-degree network. "
                    "You can't trade with them yet."
                )

def page_my_listings():
    require_login()
    st.subheader("My listings")

    listings = get_my_listings(st.session_state.user_id)
    if not listings:
        st.info("You don't have any listings yet.")
        return

    for row in listings:
        box = st.container(border=True)
        with box:
            st.markdown(f"**{row['title']}**")
            meta_cols = st.columns(3)
            with meta_cols[0]:
                st.write(f"Price: ${row['price']:,.2f} {row['currency']}")
            with meta_cols[1]:
                st.write(f"Status: {row['status']}")
            with meta_cols[2]:
                st.write(f"Created: {row['created_at'][:10]}")

            if row["description"]:
                st.write(row["description"])

def page_network():
    require_login()
    st.subheader("Your Circle")

    user = get_user_by_id(st.session_state.user_id)
    st.write(f"Logged in as **{user['name']}** (`{user['email']}`)")

    # Invite codes
    st.markdown("### Invite friends")
    if st.button("Generate new invite code"):
        code = generate_invite_code(st.session_state.user_id)
        st.success(f"Invite code created: `{code}`")

    codes = get_invite_codes_for_user(st.session_state.user_id)
    if codes:
        st.write("Your invite codes:")
        for c in codes:
            used = "✅ used" if c["used_by"] else "🟢 unused"
            st.code(f"{c['code']}  ({used})")
    else:
        st.caption("You don't have any invite codes yet.")

    # Direct friends
    st.markdown("### Direct connections")
    friend_ids = list(get_friends(st.session_state.user_id))
    if not friend_ids:
        st.caption("No connections yet. Invite someone to start your circle.")
        return

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        f"SELECT id, name, email FROM users WHERE id IN ({','.join('?'*len(friend_ids))})",
        friend_ids,
    )
    friends = cur.fetchall()
    conn.close()

    for f in friends:
        st.write(f"- **{f['name']}** (`{f['email']}`)")

# ---------------------------
# Main app
# ---------------------------

def main():
    st.set_page_config(page_title="Circle Marketplace", layout="wide")
    init_db()

    if "user_id" not in st.session_state:
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.session_state.user_email = None

    st.title("Circle Marketplace (MVP)")
    st.caption("Invite-only marketplace for high-value items, limited to your circle and friends-of-friends.")

    if st.session_state.user_id is None:
        show_auth_ui()
        return

    # Sidebar navigation
    with st.sidebar:
        st.markdown(f"**Hi, {st.session_state.user_name}** 👋")
        page = st.radio(
            "Navigation",
            ["Browse", "Create listing", "My listings", "My network"],
        )
        if st.button("Log out", use_container_width=True):
            st.session_state.user_id = None
            st.session_state.user_name = None
            st.session_state.user_email = None
            st.experimental_rerun()

    if page == "Browse":
        page_browse_listings()
    elif page == "Create listing":
        page_create_listing()
    elif page == "My listings":
        page_my_listings()
    elif page == "My network":
        page_network()

if __name__ == "__main__":
    main()
