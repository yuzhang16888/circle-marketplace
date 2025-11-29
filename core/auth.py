def ensure_user_logged_in():
    """
    Invite-only auth flow.

    - Existing users: login with email only.
    - New users: must provide a valid invite code.
    """
    if "user" in st.session_state:
        return st.session_state["user"]

    st.header("Welcome to Circle Marketplace")

    mode = st.radio("Select:", ["Sign Up", "Log In"], horizontal=True)

    email = st.text_input("Email")

    # ---- SIGN UP ----
    if mode == "Sign Up":
        invite_code = st.text_input(
            "Invite code (required)",
            help="Existing members can share invite codes via their Profile page.",
        )

        if st.button("Create Account"):
            if not email:
                st.error("Please enter your email.")
                return

            existing = get_user_by_email(email.strip().lower())
            if existing:
                st.error("This email already has an account. Please switch to Log In.")
                return

            if not invite_code:
                st.error("Invite code is required to join Circle.")
                return

            invite = get_invite_by_code(invite_code.strip())
            if not invite:
                st.error("Invalid invite code. Please check with your friend.")
                return

            # Create the new user
            new_user_id = create_user(email.strip().lower())

            inviter_id = invite["inviter_user_id"]
            add_friend(inviter_id, new_user_id)
            add_friend(new_user_id, inviter_id)

            st.session_state["user"] = {
                "id": new_user_id,
                "email": email.strip().lower(),
            }

            st.success("Welcome to Circle! Your account has been created.")
            st.rerun()

    # ---- LOG IN ----
    else:
        if st.button("Log In"):
            if not email:
                st.error("Please enter your email.")
                return

            existing = get_user_by_email(email.strip().lower())
            if not existing:
                st.error("No account found with this email. Please switch to Sign Up.")
                return

            st.session_state["user"] = {
                "id": existing["id"],
                "email": existing["email"],
            }
            st.rerun()

    return None
