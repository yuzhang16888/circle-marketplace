from typing import Optional

import streamlit as st
import stripe

from core.auth import get_current_user
from core.db import get_db
from core.models import User

stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]


def render(user: Optional[dict] = None):
    if user is None:
        user = get_current_user()

    if not user:
        st.error("You need to be logged in to use this page.")
        st.stop()

    st.header("🔗 Stripe Connect – Test Page")

    default_email = user.get("email") if isinstance(user, dict) else None
    email = st.text_input(
        "Seller email for Stripe test account",
        value=default_email or "test-seller@example.com",
    )

    if st.button("Create test Stripe Connect account"):
        try:
            account = stripe.Account.create(
                type="standard",
                email=email,
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                },
                metadata={"circle_user_id": str(user.get("id"))},
            )

            # 🔹 save Stripe account ID to this user in DB
            db = get_db()
            db_user = db.query(User).filter(User.id == user["id"]).first()
            if db_user is None:
                st.error("Could not find your user in database.")
                return

            db_user.stripe_account_id = account.id
            # for now we just set onboarded=False; later we can verify with Stripe
            db_user.stripe_onboarded = False
            db.commit()

            st.success(
                f"✅ Created Stripe account `{account.id}` and saved it to your profile."
            )

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
