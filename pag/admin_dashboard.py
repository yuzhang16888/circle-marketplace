# pag/admin_dashboard.py
import streamlit as st
from typing import Dict
from core import api_client


def render(user: Dict):
    """
    Admin Dashboard: for now focuses on invite management.
    (Friend manager removed temporarily to keep things stable.)
    """
    st.header("Admin Dashboard")

    st.markdown(
        f"Current user: **{user.get('email', '')}** (id: `{user.get('id', '—')}`)"
    )

    st.divider()

    col_left, col_right = st.columns([2, 3])

    # -------- LEFT: create invites --------
    with col_left:
        st.subheader("Invite a friend to Circle")

        invite_email = st.text_input("Friend's email", key="invite_email")

        if st.button("Create invite", key="invite_button"):
            if not invite_email:
                st.error("Please enter an email.")
            else:
                try:
                    resp = api_client.create_invite(
                        invite_email,
                        invited_by_id=user.get("id"),
                    )
                    st.success(
                        f"Invite created for {invite_email} (ID: {resp['invite_id']})."
                    )
                except Exception as e:
                    st.error(f"Failed to create invite: {e}")

        st.caption(
            "Anyone you invite can sign up using that exact email address. "
            "Uninvited emails will be blocked at signup."
        )

    # -------- RIGHT: list existing invites --------
    with col_right:
        st.subheader("Existing invites")

        try:
            data = api_client.list_invites()
            invites = data.get("invites", [])
            if not invites:
                st.info("No invites yet.")
            else:
                st.dataframe(invites)
        except Exception as e:
            st.error(f"Failed to load invites: {e}")

    st.markdown("---")
    st.caption("Friend manager features can be added back later on top of this.")
