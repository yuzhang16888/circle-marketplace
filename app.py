# app.py
from core.api_client import backend_ping
import streamlit as st
from core.db import init_db
from core.auth import ensure_user_logged_in
from pag import home, create_listing, my_listings, admin_dashboard, profile, cart, checkout

NAV_PAGES = [
    "Home",
    "Create Listing",
    "My Listings",
    "Cart",
    "Checkout",
    "Admin Dashboard",
    "Profile & Friends",
]

def main():
    init_db()
    st.set_page_config(page_title="Circle Marketplace", layout="wide")

    # Backend status check
    if backend_ping():
        st.sidebar.success("Backend: online ✅")
    else:
        st.sidebar.error("Backend: offline ❌")


    # 2) Auth
    user = ensure_user_logged_in()
    if user is None:
        st.stop()

    # 3) Navigation – our own nav state
    if "main_nav" not in st.session_state:
        st.session_state["main_nav"] = "Home"

    # keep widget key separate from our internal key
    current_index = NAV_PAGES.index(st.session_state["main_nav"])

    page = st.sidebar.radio(
        "Navigation",
        NAV_PAGES,
        index=current_index,
        key="nav_widget",           # 🔴 changed: no longer "main_nav"
    )

    # sync widget selection back into our nav state
    if page != st.session_state["main_nav"]:
        st.session_state["main_nav"] = page

    # route based on our own nav state
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

if __name__ == "__main__":
    main()
