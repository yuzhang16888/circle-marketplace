# core/auth.py
import streamlit as st
from core.db import insert_user_if_not_exists

def ensure_user_logged_in():
    if "user" in st.session_state:
        return st.session_state["user"]

    st.header("Welcome to Circle Marketplace")

    tab_login, _ = st.tabs(["Login", "Sign up"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            user_id = insert_user_if_not_exists(email)
            st.session_state["user"] = {
                "id": user_id,
                "email": email,
            }
            st.rerun()

    return None
