# app.py
import streamlit as st
from core.db import init_db
from core.auth import ensure_user_logged_in
from pag import home, create_listing, my_listings, admin_dashboard, profile


def main():
    init_db()
    st.set_page_config(page_title="Circle Marketplace", layout="wide")

    # 1) Make sure DB exists
    

    # 2) Auth
    user = ensure_user_logged_in()
    if user is None:
        st.stop()

    # 3) Navigation
    st.sidebar.title("Circle Marketplace")
    
    page = st.sidebar.radio(
        "Go to",
        ["Home", "Create Listing", "My Listings", "Profile & Friends", "Admin Dashboard"],
        key="nav_page",
)

    # 4) Routing
    if page == "Home":
        home.render(user)
    elif page == "Create Listing":
        create_listing.render(user)
    elif page == "My Listings":
        my_listings.render(user)
    elif page == "Profile & Friends":
        profile.render(user)
    elif page == "Admin Dashboard":
        admin_dashboard.render(user)

if __name__ == "__main__":
    main()
