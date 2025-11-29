# app.py
import streamlit as st
from core.db import init_db
from core.auth import ensure_user_logged_in
from pag import home, create_listing, my_listings, admin_dashboard, profile,cart,checkout


def main():
    init_db()
    st.set_page_config(page_title="Circle Marketplace", layout="wide")

    # 1) Make sure DB exists
    

    # 2) Auth
    user = ensure_user_logged_in()
    if user is None:
        st.stop()

    # 3) Navigation
        # Ensure nav state exists
    if "main_nav" not in st.session_state:
        st.session_state["main_nav"] = "Home"

    page = st.sidebar.radio(
        "Navigation",
        [
            "Home",
            "Create Listing",
            "My Listings",
            "Cart",
            "Checkout",
            "Admin Dashboard",
            "Profile & Friends",
        ],
        key="main_nav",
    )


    # 4) Routing
    if page == "Home":
        home.render(user)
    elif page == "Create Listing":
        create_listing.render(user)
    elif page == "My Listings":
        my_listings.render(user)
    elif page == "Cart":
        cart.render(user)
    elif page=="Checkout":
        checkoout.render(user)
    elif page == "Profile & Friends":
        profile.render(user)
    elif page == "Admin Dashboard":
        admin_dashboard.render(user)


if __name__ == "__main__":
    main()
