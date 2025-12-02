import streamlit as st
import stripe

# 1) Set Stripe secret key from st.secrets
stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

st.title("🔗 Stripe Connect – Test Page")

st.write("This page is only for testing that Stripe Connect works.")

# 2) Ask for an email (you can use your own email for testing)
email = st.text_input("Seller email (for test account)", value="test-seller@example.com")

if st.button("Create test Stripe Connect account"):
    try:
        # 3) Create a Stripe Connect Standard account
        account = stripe.Account.create(
            type="standard",
            email=email,
            capabilities={
                "card_payments": {"requested": True},
                "transfers": {"requested": True},
            },
        )

        st.success(f"Created Stripe account: {account.id}")

        # 4) Create an onboarding link so the seller can finish setup
        account_link = stripe.AccountLink.create(
            account=account.id,
            refresh_url="http://localhost:8501/test_stripe_connect",
            return_url="http://localhost:8501/test_stripe_connect",
            type="account_onboarding",
        )

        st.write("Onboarding link (click to open in new tab):")
        st.markdown(f"[Open Stripe onboarding]({account_link['url']})")

    except Exception as e:
        st.error(f"Error talking to Stripe: {e}")
