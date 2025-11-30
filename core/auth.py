# core/auth.py
import streamlit as st
from typing import Optional
from core import api_client


USER_SESSION_KEY = "user"


def get_current_user() -> Optional[dict]:
    return st.session_state.get(USER_SESSION_KEY)


def logout():
    if USER_SESSION_KEY in st.session_state:
        del st.session_state[USER_SESSION_KEY]


def ensure_user_logged_in() -> Optional[dict]:
    """
    Show login / signup UI until the user is authenticated via backend.
    Returns the user dict (id, email, full_name) or None if user bails out.
    """
    user = get_current_user()
    if user:
        return user

    st.sidebar.markdown("### Sign in to Circle")

    tab_login, tab_signup = st.tabs(["Log in", "Sign up"])

    # ---- LOGIN TAB ----
    with tab_login:
        st.subheader("Welcome back")
        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_password")

        if st.button("Log in", key="login_button"):
            if not login_email or not login_password:
                st.error("Please enter both email and password.")
            else:
                try:
                    resp = api_client.login_user(login_email, login_password)
                    st.session_state[USER_SESSION_KEY] = resp["user"]
                    st.success("Logged in successfully.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Login failed: {e}")

    # ---- SIGNUP TAB ----
    with tab_signup:
        st.subheader("Create your Circle account")

        signup_full_name = st.text_input("Full name", key="signup_full_name")
        signup_email = st.text_input("Email", key="signup_email")
        signup_password = st.text_input("Password", type="password", key="signup_password")

        if st.button("Sign up", key="signup_button"):
            if not signup_email or not signup_password:
                st.error("Email and password are required.")
            else:
                try:
                    resp = api_client.register_user(signup_email, signup_password, signup_full_name)
                    st.success("Account created! You can now log in.")
                except Exception as e:
                    st.error(f"Sign up failed: {e}")

    st.stop()
