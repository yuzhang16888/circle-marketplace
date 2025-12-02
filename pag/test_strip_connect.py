# pag/test_strip_connect.py

from typing import Optional

import streamlit as st
import stripe

from core.auth import get_current_user
from core.db import get_user_by_id, update_user_stripe_account

stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]


def render(user: Optional[dict] = None):
    """
    Test page for Stripe Connect onboarding using sqlite3-based DB helpers.
    """
    if user is None:
        user = get_current_user()

    if not user:
        st.error("You need to be logged in to use this page.")
        st.stop()

    st.header("🔗 Stripe Connect – Test Page")

    # user might be a dict or a Row; handle both
    user_id = user.get("id") if isinstance(user, dict) else user["id"]
    user_row = get_user_by_id(user_id)
    email_from_db = user_row["email"] if user_row else None

    default_email = email_from_db or (user.get("email") if isinstance(user, dict) else None)
    email = st.text_input(
        "Seller email for Stripe test account",
        value=default_email or "test-seller@example.com",
    )

    if st.button("Create test Stripe Connect account"):
        try:
            # 1) Create Stripe Connect Standard account
            account = stripe.Account.create(
                type="standard",
                email=email,
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                },
                metadata={"circle_user_id": str(user_id)},
            )

            # 2) Save Stripe account ID in our sqlite users table
            update_user_stripe_account(user_id=user_id, stripe_account_id=account.id, onboarded=False)

            st.success(
                f"✅ Created Stripe account `{account.id}` and saved it to your profile."
            )

            # 3) Generate onboarding link
            account_link = stripe.AccountLink.create(
                account=account.id,
                refresh_url="http://localhost:8501/test_strip_connect",
                return_url="http://localhost:8501/test_strip_connect",
                type="account_onboarding",
            )

            st.write("Onboarding link (opens Stripe in a new tab):")
            st.markdown(f"[Open Stripe onboarding]({account_link['url']})")

        except Exception as e:
            st.error(f"Error talking to Stripe: {e}")
