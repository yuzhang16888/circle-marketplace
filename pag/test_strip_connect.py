# pages/test_stripe_connect.py

from typing import Optional

import streamlit as st
import stripe

from core.auth import get_current_user  # same pattern as profile.py

# Use your secret key from st.secrets
stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]


def render(user: Optional[dict] = None):
    """
    Test page for Stripe Connect onboarding.
    Only for internal testing – not user-facing yet.
    """
    # Make sure we have a logged-in user, same logic as profile.py
    if user is None:
        user = get_current_user()

    if not user:
        st.error("You need to be logged in to use this page.")
        st.stop()

    st.header("🔗 Stripe Connect – Test Page")
    st.write(
        "This page is only for testing that we can talk to Stripe Connect and "
        "create an onboarding link for a seller."
    )

    # Default email: current user's email, but you can override it
    default_email = user.get("email") if isinstance(user, dict) else None
    email = st.text_input(
        "Seller email for Stripe test account",
        value=default_email or "test-seller@example.com",
    )

    if st.button("Create test Stripe Connect account"):
        try:
            # 1) Create a Stripe Connect Standard account
            account = stripe.Account.create(
                type="standard",
                email=email,
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                },
                metadata={"circle_user_id": str(user.get("id")) if isinstance(user, dict) else ""},
            )

            st.success(f"✅ Created Stripe account: `{account.id}`")

            # 2) Create an onboarding link so the seller can finish setup
            account_link = stripe.AccountLink.create(
                account=account.id,
                refresh_url="http://localhost:8501/test_stripe_connect",
                return_url="http://localhost:8501/test_stripe_connect",
                type="account_onboarding",
            )

            st.write("Onboarding link (opens Stripe in a new tab):")
            st.markdown(f"[Open Stripe onboarding]({account_link['url']})")

        except Exception as e:
            st.error(f"Error talking to Stripe: {e}")
