# pag/profile.py
import streamlit as st
from core.db import (
    get_user_by_id,
    update_user_display_name,
    create_invite_code,
    get_invite_codes_for_user,
)


def render(user):
    st.header("Profile & Settings")

    # Load latest user data from DB
    db_user = get_user_by_id(user["id"])
    if not db_user:
        st.error("User not found in database.")
        return

    st.subheader("Basic Info")

    with st.form("profile_basic_form"):
        email = st.text_input("Email (read-only)", value=db_user["email"], disabled=True)
        display_name = st.text_input(
            "Display name",
            value=db_user["display_name"] or db_user["email"].split("@")[0],
        )
        submitted = st.form_submit_button("Save changes")

    if submitted:
        update_user_display_name(user["id"], display_name)
        st.success("Profile updated successfully. ✅")

    st.divider()

    st.subheader("Invite Friends to Circle")

    if st.button("Generate new invite code"):
        code = create_invite_code(user["id"])
        st.success(f"New invite code created: `{code}`")
        st.caption("You can copy this code and share it with your friend via text / email.")

    invite_rows = get_invite_codes_for_user(user["id"])
    if invite_rows:
        st.markdown("**Your invite codes:**")
        for row in invite_rows:
            st.code(row["code"])
            st.caption(f"Created at: {row['created_at']}")
    else:
        st.info("You haven't created any invite codes yet.")
