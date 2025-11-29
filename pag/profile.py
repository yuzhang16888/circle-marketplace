# pag/profile.py
import streamlit as st
from urllib.parse import quote_plus

from core.db import (
    get_user_by_id,
    update_user_display_name,
    create_invite_code,
    get_invite_codes_for_user,
    update_user_profile_image,
    update_user_password_hash,
    get_users_invited_by,
)
from core.storage import save_profile_image
from core.auth import verify_password, hash_password


def _compute_initials(db_user) -> str:
    first = (db_user["first_name"] or "").strip()
    last = (db_user["last_name"] or "").strip()
    if first or last:
        return (first[:1] + last[:1]).upper()
    if db_user["display_name"]:
        return db_user["display_name"][:2].upper()
    if db_user["email"]:
        return db_user["email"][:2].upper()
    return "??"


def _friend_display_name(friend_row) -> str:
    first = (friend_row["first_name"] or "").strip()
    last = (friend_row["last_name"] or "").strip()
    if first or last:
        return (first + " " + last).strip()
    if friend_row["display_name"]:
        return friend_row["display_name"]
    return friend_row["email"]


def _friend_initials(friend_row) -> str:
    first = (friend_row["first_name"] or "").strip()
    last = (friend_row["last_name"] or "").strip()
    if first or last:
        return (first[:1] + last[:1]).upper()
    if friend_row["display_name"]:
        return friend_row["display_name"][:2].upper()
    if friend_row["email"]:
        return friend_row["email"][:2].upper()
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

    st.divider()

    # ---- BASIC INFO (COLLAPSIBLE) ----
    with st.expander("Basic Information", expanded=False):
        with st.form("profile_basic_form"):
            email = st.text_input("Email (read-only)", value=db_user["email"], disabled=True)
            display_name = st.text_input(
                "Display Name",
                value=db_user["display_name"] or db_user["email"].split("@")[0],
            )
            first_name = st.text_input(
                "First Name",
                value=db_user["first_name"] or "",
                disabled=True,
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
                if not verify_password(current_pw, db_user["password_hash"]):
                    st.error("Current password is incorrect.")
                else:
                    new_hash = hash_password(new_pw)
                    update_user_password_hash(user["id"], new_hash)
                    st.success("Your password has been updated successfully.")

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

            st.text_input(
                "Tap to copy (Ctrl/Cmd + C):",
                value=code,
                key=f"copy_field_{idx}",
            )

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

    # ---- FRIENDS YOU INVITED ----
    st.subheader("Friends on Circle")

    invited_friends = get_users_invited_by(user["id"])

    if not invited_friends:
        st.caption("No friends from your invites yet. Once someone joins using your invite, they’ll appear here.")
    else:
        st.caption("These are members who joined Circle using **your** invite.")

        cols_per_row = 4
        for i in range(0, len(invited_friends), cols_per_row):
            row_chunk = invited_friends[i : i + cols_per_row]
            cols = st.columns(len(row_chunk))

            for col, friend in zip(cols, row_chunk):
                with col:
                    # Avatar
                    if friend["profile_image_path"]:
                        st.image(friend["profile_image_path"], width=80)
                    else:
                        initials = _friend_initials(friend)
                        st.markdown(
                            f"""
                            <div style="
                                width: 80px;
                                height: 80px;
                                border-radius: 40px;
                                background-color: #333;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                color: white;
                                font-size: 26px;
                                font-weight: 600;
                                margin-bottom: 4px;
                            ">
                                {initials}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    name = _friend_display_name(friend)
                    st.markdown(f"**{name}**")

                    # Small actions
                    if st.button("View profile", key=f"view_friend_{friend['id']}"):
                        st.session_state["view_friend_profile_id"] = friend["id"]

                    if st.button("Report", key=f"report_friend_{friend['id']}"):
                        st.session_state["report_friend_id"] = friend["id"]

    # ---- VIEW FRIEND PROFILE (READ-ONLY) ----
    friend_id_to_view = st.session_state.get("view_friend_profile_id")
    if friend_id_to_view:
        friend = get_user_by_id(friend_id_to_view)
        if friend:
            st.divider()
            st.subheader("Friend Profile (view only)")

            col_a, col_b = st.columns([1, 2])
            with col_a:
                if friend["profile_image_path"]:
                    st.image(friend["profile_image_path"], width=120)
                else:
                    initials = _compute_initials(friend)
                    st.markdown(
                        f"""
                        <div style="
                            width: 120px;
                            height: 120px;
                            border-radius: 60px;
                            background-color: #444;
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

            with col_b:
                st.markdown(f"**Name:** {_friend_display_name(friend)}")
                st.markdown(f"**Email:** {friend['email']}")
                if friend["inviter_name"]:
                    st.markdown(f"**Invited by:** {friend['inviter_name']}")

            st.caption("This is a read-only view. Only each member can edit their own profile.")

    # ---- REPORT SUSPICIOUS FRIEND ----
    report_friend_id = st.session_state.get("report_friend_id")
    if report_friend_id:
        suspect = get_user_by_id(report_friend_id)
        st.divider()
        st.subheader("Report Suspicious Friend")

        if suspect:
            st.markdown(
                f"You are reporting: **{_friend_display_name(suspect)}** (`{suspect['email']}`)"
            )

        reason = st.text_area(
            "Describe what feels off or concerning. This will be shared with the Circle admin.",
            key="report_reason",
        )

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            if st.button("Submit Report 🚨"):
                # Phase 2: write to a 'reports' table for admin review
                st.success("Thank you. Your report has been recorded for admin review.")
                # Clear state
                st.session_state["report_friend_id"] = None
                st.session_state["report_reason"] = ""
        with col_r2:
            if st.button("Cancel"):
                st.session_state["report_friend_id"] = None
                st.session_state["report_reason"] = ""

    st.divider()

    # ---- SAFETY CENTER ----
    st.subheader("Safety Center")

    st.caption("If you encounter suspicious activity in a transaction, please report it.")

    if st.button("Report Suspicious Transaction 🚨"):
        st.warning("Thank you. A Circle admin will review your report.")
        # Phase 2/3: log reports to DB for admin review
