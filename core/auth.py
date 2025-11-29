# core/auth.py
import os
import hashlib
import binascii
import streamlit as st
import hmac

from core.db import (
    get_user_by_email,
    create_user,
    get_invite_by_code,
    add_friend,
    update_user_profile_image,
)
from core.storage import save_profile_image


# ---------- PASSWORD HELPERS ----------

def hash_password(password: str) -> str:
    """Hash password with PBKDF2 + salt. Stored as 'salt$hash'."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{binascii.hexlify(salt).decode()}${binascii.hexlify(dk).decode()}"

def verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        return False
    try:
        salt_hex, hash_hex = stored.split("$", 1)
        salt = binascii.unhexlify(salt_hex)
        expected = binascii.unhexlify(hash_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        # Use hmac.compare_digest for a constant-time comparison
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False



def ensure_user_logged_in():
    """
    Invite-only auth flow with stronger identity:

    LOG IN (existing user)
      - email + password

    SIGN UP (new user, with invite code)
      - first name, last name, phone, email
      - who invited you (full name)
      - password + confirm password
      - optional profile picture
      - valid invite code required
    """
    # If already logged in, just return the user
    if "user" in st.session_state:
        return st.session_state["user"]

    st.header("Welcome to Circle Marketplace")

    # Order is explicit: first "Log In", then "Sign Up"
    mode = st.radio(
        "Select:",
        ["Log In", "Sign Up"],
        horizontal=True,
        index=0,
    )

     # ---------- LOG IN FLOW ----------
    if mode == "Log In":
        st.subheader("Log in to Circle")

        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        st.caption(
            "Forgot password? For now, please email our team from your registered address "
            "with the subject **“Circle password reset”**, and we’ll help you reset it."
        )
        st.markdown(
            "[Compose reset email 📧](mailto:?subject=Circle%20password%20reset&body="
            "Hi%20Circle%20team%2C%0A%0AI%27d%20like%20to%20reset%20my%20password."
            "%20My%20registered%20email%20is%3A%20)"
        )

        if st.button("Log In"):
            if not email or not password:
                st.error("Please enter both email and password.")
                return None

            email_clean = email.strip().lower()
            existing = get_user_by_email(email_clean)
            if not existing:
                st.error("No account found with this email. Please switch to Sign Up.")
                return None

            stored_hash = existing["password_hash"]
            if not stored_hash:
                st.error(
                    "This account was created before passwords were required. "
                    "Please contact support or sign up again with a new email."
                )
                return None

            if not verify_password(password, stored_hash):
                st.error("Incorrect password. Please try again.")
                return None

            user = {
                "id": existing["id"],
                "email": existing["email"],
            }
            st.session_state["user"] = user
            st.success("Logged in successfully. Welcome back to Circle. ✨")
            return user

        return None


    # ---------- SIGN UP FLOW ----------
    else:
        st.subheader("Create your Circle account")

        first_name = st.text_input("First name")
        last_name = st.text_input("Last name")
        phone = st.text_input("Mobile phone")
        inviter_full_name = st.text_input("Who invited you? (full name)")
        email = st.text_input("Email")

        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm password", type="password")

        invite_code = st.text_input(
            "Invite code (required)",
            help="Your inviter can find their codes under Profile & Friends → Invite Friends to Circle.",
        )

        profile_file = st.file_uploader(
            "Profile picture (optional)",
            type=["jpg", "jpeg", "png"],
        )

        if st.button("Create Account"):
            # Basic validation
            if not first_name or not last_name or not phone or not email or not inviter_full_name:
                st.error("Please fill in all required fields (name, phone, email, inviter).")
                return None

            if not password or not confirm_password:
                st.error("Please enter and confirm your password.")
                return None

            if password != confirm_password:
                st.error("Passwords do not match.")
                return None

            if len(password) < 8:
                st.error("Password must be at least 8 characters long.")
                return None

            if not invite_code:
                st.error("Invite code is required to join Circle.")
                return None

            email_clean = email.strip().lower()
            existing = get_user_by_email(email_clean)
            if existing:
                st.error("This email already has an account. Please switch to Log In.")
                return None

            invite = get_invite_by_code(invite_code.strip())
            if not invite:
                st.error("Invalid invite code. Please check with your friend.")
                return None

            # Hash password
            pw_hash = hash_password(password)

            # Create the new user
            new_user_id = create_user(
                email=email_clean,
                password_hash=pw_hash,
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                phone=phone.strip(),
                inviter_name=inviter_full_name.strip(),
            )

            # Save profile image if provided
            if profile_file is not None:
                image_path = save_profile_image(new_user_id, profile_file)
                update_user_profile_image(new_user_id, image_path)

            # Automatically connect inviter and new user as friends (both ways)
            inviter_id = invite["inviter_user_id"]
            add_friend(inviter_id, new_user_id)
            add_friend(new_user_id, inviter_id)

            new_user = {
                "id": new_user_id,
                "email": email_clean,
            }
            st.session_state["user"] = new_user

            st.success(
                "Your Circle account has been created successfully. "
                "You're now logged in and can start exploring the marketplace. ✨"
            )
            return new_user

        return None
