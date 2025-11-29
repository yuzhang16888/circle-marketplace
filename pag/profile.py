# pag/profile.py
import streamlit as st
from urllib.parse import quote_plus

from core.db import (
    get_user_by_id,
    update_user_display_name,
    create_invite_code,
    get_invite_codes_for_user,
    update_user_profile_image,
    update_user_password_hash,   # 👈 add this
)
from core.storage import save_profile_image
from core.auth import verify_password, hash_password  # 👈 add this



def _compute_initials(db_user) -> str:
    first = (db_user["first_name"] or "").strip()
    last = (db_user["last_name"] or "").strip()
    if first or last:
        return (first[:1] + last[:1]).upper()
    # Fallback to display_name or email
    if db_user["display_name"]:
        return db_user["display_name"][:2].upper()
    if db_user["email"]:
        return db_user["email"][:2].upper()
    return "??"


def render(user):
    st.header("Profile & Friends")

    # Load latest DB values
    db_user = get_user_by_id(user["id"])
    if not db_user:
        st.error("User not found.")
        return

    # ---- PROFILE PHOTO ----
    st.subheader("Profile Photo")

    col_a, col_b = st.columns([1, 2])
    with col_a:
        if db_user["profile_image_path"]:
            st.image(db_user["profile_image_path"], width=120)
        else:
            initials = _compute_initials(db_user)
            st.markdown(
                f"""
                <div style="
                    width: 120px;
                    height: 120px;
                    border-radius: 60px;
                    background-color: #222;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 40px;
                    font-weight: 600;
                ">
                    {initials}
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption("No profile photo yet — using your initials for now.")

    with col_b:
        profile_file = st.file_uploader(
            "Upload / change your profile picture",
            type=["jpg", "jpeg", "png"],
            key="profile_upload",
        )
        if st.button("Save Profile Picture"):
            if profile_file is None:
                st.warning("Please choose an image file first.")
            else:
                path = save_profile_image(user["id"], profile_file)
                update_user_profile_image(user["id"], path)
                st.success("Profile picture updated.")
                # You can uncomment the next line if you want immediate visual refresh:
                # st.rerun()

    st.divider()

    # ---- BASIC INFO ----
    st.subheader("Basic Information")

    with st.form("profile_basic_form"):
        email = st.text_input("Email (read-only)", value=db_user["email"], disabled=True)
        display_name = st.text_input(
            "Display Name",
            value=db_user["display_name"] or db_user["email"].split("@")[0],
        )
        first_name = st.text_input(
            "First Name",
            value=db_user["first_name"] or "",
            disabled=True,  # keep as record of signup; editable later if needed
        )
        last_name = st.text_input(
            "Last Name",
            value=db_user["last_name"] or "",
            disabled=True,
        )
        phone = st.text_input(
            "Mobile Phone",
            value=db_user["phone"] or "",
            disabled=True,
        )
        inviter_name = st.text_input(
            "Who Invited You (recorded at signup)",
            value=db_user["inviter_name"] or "",
            disabled=True,
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

        st.divider()

    # ---- SECURITY / PASSWORD ----
    st.subheader("Security")

    with st.expander("Change password", expanded=False):
        current_pw = st.text_input("Current password", type="password", key="pw_current")
        new_pw = st.text_input("New password", type="password", key="pw_new")
        new_pw_confirm = st.text_input("Confirm new password", type="password", key="pw_new_confirm")

        if st.button("Update Password"):
            if not current_pw or not new_pw or not new_pw_confirm:
                st.error("Please fill in all password fields.")
            elif new_pw != new_pw_confirm:
                st.error("New passwords do not match.")
            elif len(new_pw) < 8:
                st.error("New password must be at least 8 characters long.")
            else:
                # Verify current password
                if not verify_password(current_pw, db_user["password_hash"]):
                    st.error("Current password is incorrect.")
                else:
                    new_hash = hash_password(new_pw)
                    update_user_password_hash(user["id"], new_hash)
                    st.success("Your password has been updated successfully.")


    # ---- SUSPICIOUS REPORT ----
    st.subheader("Safety Center")

    st.caption("If you encounter suspicious activity, please report it.")

    if st.button("Report Suspicious Transaction 🚨"):
        st.warning("Thank you. A Circle admin will review your report.")
        # Phase 2/3: log reports to DB for admin review
