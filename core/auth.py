# core/auth.py
import streamlit as st
from core.db import (
    get_user_by_email,
    create_user,
    get_invite_by_code,
    add_friend,
)


def ensure_user_logged_in():
    """
    Invite-only auth flow.

    - Existing users: login with email only.
    - New users: must provide a valid invite code.
    """
    if "user" in st.session_state:
        return st.session_state["user"]

    st.header("Welcome to Circle Marketplace")

    st.markdown(
        "This is an invite-only community. "
        "If you're new here, you'll need an invite code from an existing member."
    )

    email = st.text_input("Email")
    invite_code = st.text_input(
        "Invite code (required if this is your first time here)",
        help="Existing members can generate invite codes from their Profile / Settings page.",
    )

    if st.button("Continue"):
        if not email:
            st.error("Please enter your email.")
            return

        existing = get_user_by_email(email.strip().lower())

        # ---- Existing user: just log in ----
        if existing:
            st.session_state["user"] = {
                "id": existing["id"],
                "email": existing["email"],
            }
            st.rerun()
            return

        # ---- New user: require invite code ----
        if not invite_code:
            st.error(
                "It looks like you're new here. "
                "You'll need a valid invite code to join Circle."
            )
            return

        invite = get_invite_by_code(invite_code.strip())
        if not invite:
            st.error("That invite code is not valid. Please check with your friend.")
            return

        # Create the new user
        new_user_id = create_user(email.strip().lower())

        # Automatically connect inviter and new user as friends (both ways)
        inviter_id = invite["inviter_user_id"]
        add_friend(inviter_id, new_user_id)
        add_friend(new_user_id, inviter_id)

        st.session_state["user"] = {
            "id": new_user_id,
            "email": email.strip().lower(),
        }

        st.success("Welcome to Circle! Your account has been created via invite. ✨")
        st.rerun()

    return None
