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

    # Load latest DB values
    db_user = get_user_by_id(user["id"])
    if not db_user:
        st.error("User not found.")
        return

    # ---- BASIC INFO ----
    st.subheader("Basic Information")
    with st.form("profile_basic_form"):
        email = st.text_input("Email (read-only)", value=db_user["email"], disabled=True)
        display_name = st.text_input("Display Name", value=db_user["display_name"])
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
        for row in invite_rows:
            code = row["code"]
            st.code(code)

            # Sharing buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"[Copy 🔗](javascript:navigator.clipboard.writeText('{code}'))")

            with col2:
                mail_body = f"Join me on Circle Marketplace! Use my invite code: {code}"
                mailto = f"mailto:?subject=Circle Invite&body={mail_body}"
                st.markdown(f"[Email 📧]({mailto})")

            with col3:
                sms_body = f"Join me on Circle Marketplace! Invite code: {code}"
                sms = f"sms:?body={sms_body}"
                st.markdown(f"[SMS 📱]({sms})")

            st.caption(f"Created at: {row['created_at']}")

    else:
        st.info("You haven't created any invite codes yet.")

    st.divider()

    # ---- SUSPICIOUS REPORT ----
    st.subheader("Safety Center")

    st.caption("If you encounter suspicious activity, please report it.")

    if st.button("Report Suspicious Transaction 🚨"):
        st.warning("Thank you. A Circle admin will review your report.")
        # Later: we will log reports into DB and create an Admin review panel.
