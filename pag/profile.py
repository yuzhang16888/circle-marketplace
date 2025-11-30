# pag/profile.py
import streamlit as st
from typing import Optional
from core.auth import get_current_user, logout


def render(user: Optional[dict] = None):
    """
    Profile & Friends page.
    For now: show basic account info and a logout button.
    Later: we can add change-password and friends/referrals.
    """
    if user is None:
        user = get_current_user()

    if not user:
        st.error("You need to be logged in to see your profile.")
        st.stop()

    st.header("Profile & Friends")

    st.subheader("Your account")

    st.write(f"**Email:** {user.get('email', '')}")
    full_name = user.get("full_name") or "Not set"
    st.write(f"**Name:** {full_name}")
    st.write(f"**User ID:** {user.get('id', '—')}")

    st.markdown("---")

    st.subheader("Sign out")

    if st.button("Log out"):
        logout()
        st.success("You have been logged out.")
        st.experimental_rerun()

    st.markdown("---")
    st.caption("More profile and friend features coming soon ✨")
