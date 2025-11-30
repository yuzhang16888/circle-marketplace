# pag/profile.py
import streamlit as st
from typing import Optional
from core.auth import get_current_user, logout
from core import api_client


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
     
    #st.markdown("---")
    #st.caption("More profile and friend features coming soon ✨")
        st.markdown("---")
    st.subheader("Invite friends to Circle")

    with st.form("profile_invite_form"):
        friend_name = st.text_input("Friend's name", key="prof_invite_name")
        friend_email = st.text_input("Friend's email", key="prof_invite_email")
        submitted = st.form_submit_button("Send invite")

    if submitted:
        if not friend_email:
            st.error("Please enter your friend's email.")
        else:
            try:
                api_client.create_invite(
                    email=friend_email,
                    name=friend_name,
                    invited_by_id=user["id"],
                )
                st.success(f"Invitation sent to {friend_email}.")
            except Exception as e:
                st.error(f"Failed to send invite: {e}")

    st.subheader("People you've invited")

    try:
        data = api_client.list_invites_by_inviter(user["id"])
        invites = data.get("invites", [])
        if not invites:
            st.info("You haven't invited anyone yet.")
        else:
            rows = []
            for inv in invites:
                status = "Joined" if inv.get("used_by_user_id") else "Pending"
                rows.append(
                    {
                        "Email": inv.get("email"),
                        "Status": status,
                        "Invited at": inv.get("created_at"),
                    }
                )
            st.table(rows)
    except Exception as e:
        st.error(f"Could not load your invites: {e}")

