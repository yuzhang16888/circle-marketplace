# app.py
from core.api_client import backend_ping,backend_db_ping
import streamlit as st
# from core.db import init_db
# init_db()
from core.auth import ensure_user_logged_in
from pag import home, create_listing, my_listings, admin_dashboard, profile, cart, checkout
            # ,test_strip_connect

from core.db import Base, engine
from core import models  # this makes sure User/Listing/Order are registered

Base.metadata.create_all(bind=engine)

import stripe



# st.write("Stripe Secret Loaded?", "STRIPE_SECRET_KEY" in st.secrets)
# st.write("Stripe Publishable Loaded?", "STRIPE_PUBLISHABLE_KEY" in st.secrets)


stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

PUBLISHABLE_KEY = st.secrets["STRIPE_PUBLISHABLE_KEY"]
SUCCESS_URL = st.secrets["STRIPE_SUCCESS_URL"]
CANCEL_URL = st.secrets["STRIPE_CANCEL_URL"]
FEE_PERCENT = st.secrets["STRIPE_PLATFORM_FEE_PERCENT"]




BASE_NAV_PAGES = [
    "Home",
    "Create Listing",
    "My Listings",
    "Cart",
    "Checkout",
   # "Admin Dashboard",
    "Profile & Friends",
    # "test_strip_connect"
]

def main():
    init_db()
    st.set_page_config(page_title="Circle Marketplace", layout="wide")

    # Backend status
    if backend_ping():
        st.sidebar.success("Backend: online ✅")
    else:
        st.sidebar.error("Backend: offline ❌")

    # DB status (Supabase)
    if backend_db_ping():
        st.sidebar.success("DB: online ✅")
    else:
        st.sidebar.error("DB: offline ❌")

    # 2) Auth
    user = ensure_user_logged_in()
    if user is None:
        st.stop()

    # 3) Navigation – build nav based on user role
    nav_pages = list(BASE_NAV_PAGES)

    # Only founder sees Admin Dashboard
    if user.get("email") == "yuzhang16888@gmail.com":
        insert_index = nav_pages.index("Profile & Friends")
        nav_pages.insert(insert_index, "Admin Dashboard")

    # Ensure nav state exists & is valid
    if "main_nav" not in st.session_state:
        st.session_state["main_nav"] = "Home"

    if st.session_state["main_nav"] not in nav_pages:
        st.session_state["main_nav"] = "Home"

    current_index = nav_pages.index(st.session_state["main_nav"])

    page = st.sidebar.radio(
        "Navigation",
        nav_pages,
        index=current_index,
        key="nav_widget",
    )

    if page != st.session_state["main_nav"]:
        st.session_state["main_nav"] = page

    # Route based on our nav state
    if st.session_state["main_nav"] == "Home":
        home.render(user)
    elif st.session_state["main_nav"] == "Create Listing":
        create_listing.render(user)
    elif st.session_state["main_nav"] == "My Listings":
        my_listings.render(user)
    elif st.session_state["main_nav"] == "Cart":
        cart.render(user)
    elif st.session_state["main_nav"] == "Checkout":
        checkout.render(user)
    elif st.session_state["main_nav"] == "Admin Dashboard":
        admin_dashboard.render(user)
    elif st.session_state["main_nav"] == "Profile & Friends":
        profile.render(user)
    # elif st.session_state["main_nav"]== "test_strip_connect":
    #     test_strip_connect.render(user)


if __name__ == "__main__":
    main()
