# pages/home.py
import streamlit as st
from core.db import init_db, insert_listing, get_listings_for_user, get_all_listings
from core.storage import save_listing_image
from core.auth import ensure_user_logged_in


def render(user):
    st.header("Circle Marketplace – Home")
    #st.write("✅ `pages.home.render()` is working.")
    if user:
        st.write(f"Logged in as: **{user.get('email', 'unknown')}**")
