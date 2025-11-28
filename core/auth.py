# core/auth.py
import streamlit as st

def ensure_user_logged_in():
    # If already logged in, just return the user
    if "user" in st.session_state:
        return st.session_state["user"]

    st.header("Welcome to Circle Marketplace")

    tab_login, tab_signup = st.tabs(["Login", "Sign up"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            # TODO: replace with real DB lookup
            # For now, we just mock a user
            st.session_state["user"] = {
                "id": 1,
                "email": email,
            }

            # 🔁 New Streamlit API: rerun
            st.rerun()

    with tab_signup:
        st.write("Sign-up UI here… (coming soon)")

    # Not logged in yet → return None so app.py can stop()
    return None
