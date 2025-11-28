# app.py
import streamlit as st

from core.db import init_db
from core.auth import ensure_user_logged_in
from pag import home
#, create_listing, my_listings, admin_dashboard

def main():
    st.set_page_config(page_title="Circle Marketplace", layout="wide")

    init_db()

    user = ensure_user_logged_in()
    if user is None:
        st.stop()

    st.sidebar.title("Circle Marketplace")
    page = st.sidebar.radio(
        "Go to",
        ["Home"],  # keep only Home until it's working
        key="nav_page",
    )

    if page == "Home":
        home.render(user)

if __name__ == "__main__":
    main()
