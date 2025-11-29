# pag/profile.py
import streamlit as st
from urllib.parse import quote_plus

from core.db import (
    get_user_by_id,
    update_user_display_name,
    create_invite_code,
    get_invite_codes_for_user,
)


def render(user):
    st.header("Profile & Friends")

    # Load latest DB values
    db_user = get_user_by_id(user["id"])
    if not db_user:
        st.error("User not found.")
        return

    # ---- BASIC INFO ----
    st.subheader("Basic Information")
    with st.form("profile_basic_form"):
        email = st.text_input("Email (read-only)", value=db_user["email"], disabled=True)
        display_name = st.text_input(
            "Display Name",
            value=db_user["display_name"] or db_user["email"].split("@")[0],
        )
        submitted = st.form_submit_button("Save Changes")

    if submitted:
        update_user_display_name(user["id"], display_name)
        st.success("Profile updated successfully!")

    st.divider()

    # ---- INVITES ----
    st.subheader("Invite Friends to Circle")

    st.info(
        """
        **Circle Community Guideline — Trust & Responsibility**

        Circle is a private, invite-only marketplace built on trust, reputation, and personal integrity.  
        When you invite someone, you are vouching for their honesty, reliability, and conduct.  
        Every member is responsible for upholding a safe, respectful trading environment —  
        for themselves and for the friends they bring in.
        """
    )

    if st.button("Generate Invite Code"):
        code = create_invite_code(user["id"])
        st.success(f"Invite code generated: `{code}`")

    invite_rows = get_invite_codes_for_user(user["id"])

    if invite_rows:
        st.markdown("### Your Invite Codes")

        for idx, row in enumerate(invite_rows):
            code = row["code"]
            st.code(code)

            # Simple copy-friendly field
            st.text_input(
                "Tap to copy (Ctrl/Cmd + C):",
                value=code,
                key=f"copy_field_{idx}",
            )

            # Build email and SMS links with URL-encoded body text
            email_body = f"Join me on Circle Marketplace! Use my invite code: {code}"
            mailto_link = (
                "mailto:?subject="
                + quote_plus("Circle Invite")
                + "&body="
                + quote_plus(email_body)
            )

            sms_body = f"Join me on Circle Marketplace! Invite code: {code}"
            sms_link = "sms:?&body=" + quote_plus(sms_body)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"[Send via Email 📧]({mailto_link})")
            with col2:
                st.markdown(f"[Send via SMS 📱]({sms_link})")

            st.caption(f"Created at: {row['created_at']}")
            st.markdown("---")
    else:
        st.info("You haven't created any invite codes yet.")

    st.divider()

    # ---- SUSPICIOUS REPORT ----
    st.subheader("Safety Center")

    st.caption("If you encounter suspicious activity, please report it.")

    if st.button("Report Suspicious Transaction 🚨"):
        st.warning("Thank you. A Circle admin will review your report.")
        # Later: we'll log this to the database for admin review
