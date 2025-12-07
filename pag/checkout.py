# pag/checkout.py
import json
import streamlit as st
import stripe

from core.db import (
    get_listings_by_ids,
    get_user_by_id,
    create_order,
    update_listing_status,
    update_order_stripe_info,
)

# ---------- CONSTANTS ----------

US_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]

CA_PROVINCES = [
    "AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU",
    "ON", "PE", "QC", "SK", "YT",
]


def _get_image_list(row):
    paths = []
    if row["image_paths"]:
        try:
            loaded = json.loads(row["image_paths"])
            if isinstance(loaded, list):
                paths = [p for p in loaded if p]
        except Exception:
            paths = []

    if not paths and row["image_path"]:
        paths = [row["image_path"]]

    return paths


def render(user):
    st.header("Checkout")

    # We expect Cart to set this
    listing_id = st.session_state.get("checkout_listing_id")
    if not listing_id:
        st.info("No item selected for checkout. Please go to Cart and choose an item.")
        return

    rows = get_listings_by_ids([listing_id])
    if not rows:
        st.error("Could not find the listing for checkout.")
        return

    listing = rows[0]
    seller_id = listing["user_id"]
    price = float(listing["price"])

    # ---------- ITEM SUMMARY ----------
    st.subheader("Item you are purchasing")

    col_img, col_txt = st.columns([1, 2])
    with col_img:
        images = _get_image_list(listing)
        if images:
            try:
                st.image(images[0], width=220)
            except Exception:
                st.caption("Image not available.")
        else:
            st.caption("No image")

    with col_txt:
        st.markdown(f"**{listing['title']}** – ${price:.0f}")

        meta_bits = []
        if listing["brand"]:
            meta_bits.append(str(listing["brand"]))
        if listing["category"]:
            meta_bits.append(str(listing["category"]))
        if listing["condition"]:
            meta_bits.append(str(listing["condition"]))
        if meta_bits:
            st.caption(" · ".join(meta_bits))

        if listing["retail_price"] is not None:
            st.caption(f"Original retail: ${float(listing['retail_price']):.0f}")

        st.write(listing["description"])

    st.divider()

    # ---------- CHECKOUT FORM ----------
    st.subheader("Shipping information")

    with st.form("checkout_form"):
        full_name = st.text_input("Full name", value="")
        address1 = st.text_input("Address line 1", value="")
        address2 = st.text_input("Address line 2 (optional)", value="")
        city = st.text_input("City", value="")

        country = st.selectbox("Country", ["United States", "Canada"], index=0)

        if country == "United States":
            state = st.selectbox("State", US_STATES, index=US_STATES.index("CA"))
        else:
            state = st.selectbox(
                "Province / Territory",
                CA_PROVINCES,
                index=CA_PROVINCES.index("ON"),
            )

        postal_code = st.text_input("ZIP / Postal code", value="")

        phone_raw = st.text_input(
            "Mobile phone",
            value="", 
            placeholder="e.g. (415) 555-1234",
        )

        st.subheader("Payment preference (for notes only)")
        payment_method = st.selectbox(
            "Preferred payment method (for seller reference)",
            ["Stripe (recommended)", "Venmo", "PayPal", "Zelle", "Cash App", "Bank transfer", "Other"],
            index=0,
        )

        buyer_note = st.text_area(
            "Notes for the seller (optional)",
            placeholder="e.g. Please ship with signature required.",
        )

        submitted = st.form_submit_button("Place order and go to payment")

    # If user hasn't submitted yet, stop here
    if not submitted:
        return

    # ---------- VALIDATION ----------
    errors = []

    if not full_name.strip():
        errors.append("Full name is required.")
    if not address1.strip():
        errors.append("Address line 1 is required.")
    if not city.strip():
        errors.append("City is required.")

    postal_code_clean = postal_code.strip().upper().replace(" ", "")

    if country == "United States":
        if not (postal_code_clean.isdigit() and len(postal_code_clean) == 5):
            errors.append("For US addresses, ZIP code must be exactly 5 digits.")
    else:  # Canada
        if len(postal_code_clean) != 6:
            errors.append(
                "For Canada, postal code should be 6 characters (e.g., A1A1A1)."
            )

    # Phone normalization: US/Canada 10 digits
    digits = "".join(ch for ch in phone_raw if ch.isdigit())
    if len(digits) != 10:
        errors.append("Please enter a valid 10-digit phone number for US/Canada.")
        formatted_phone = phone_raw.strip()
    else:
        formatted_phone = f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"

    if errors:
        for e in errors:
            st.error("Please fix the following issues:")
        for e in errors:
            st.error(f"• {e}")
        return

    # ---------- LOAD SELLER + STRIPE ACCOUNT ----------
    seller = get_user_by_id(seller_id)
    if not seller:
        st.error("Seller not found.")
        return
    # --- DEBUG: see what checkout sees for this seller ---
    try:
        st.write("DEBUG seller_id:", seller_id)
        st.write("DEBUG seller row:", dict(seller))
    except Exception:
        st.write("DEBUG seller_id:", seller_id)
        st.write("DEBUG stripe_account_id:", seller["stripe_account_id"])
        st.write("DEBUG stripe_onboarded:", seller["stripe_onboarded"])

    seller_stripe_account_id = seller["stripe_account_id"]
    if not seller_stripe_account_id:
        st.error(
            "This seller has not finished setting up Stripe payouts yet. "
            "Please ask them to complete onboarding first."
        )
        return

    # ---------- CREATE ORDER (local DB) ----------
    buyer_id = user["id"]
    total_price = price  # TODO: later add shipping / fees if needed

    order_id = create_order(
        buyer_id=buyer_id,
        seller_id=seller_id,
        listing_id=listing_id,
        total_price=total_price,
        shipping_name=full_name.strip(),
        shipping_address1=address1.strip(),
        shipping_address2=address2.strip(),
        shipping_city=city.strip(),
        shipping_state=state.strip(),
        shipping_postal_code=postal_code_clean,
        shipping_country=country,
        shipping_phone=formatted_phone,
        payment_method="Stripe",  # main actual payment channel
        buyer_note=buyer_note.strip(),
    )

    # Mark listing as reserved so it disappears from public feed
    update_listing_status(seller_id, listing_id, "reserved")

    # Remove from cart
    if "cart_listing_ids" in st.session_state:
        st.session_state["cart_listing_ids"] = [
            x for x in st.session_state["cart_listing_ids"] if x != listing_id
        ]

    # ---------- CREATE STRIPE CHECKOUT SESSION ----------
    try:
        stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]
    except Exception:
        st.error("Stripe secret key is not configured in Streamlit secrets.")
        return

    # Commission: default 10% unless overridden in secrets
    platform_fee_percent = float(st.secrets.get("STRIPE_PLATFORM_FEE_PERCENT", 10))

    amount_cents = int(round(total_price * 100))
    fee_cents = int(round(amount_cents * platform_fee_percent / 100.0))

    # Try to get buyer email from user dict (fallback to None)
    buyer_email = user.get("email") if isinstance(user, dict) else None

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": listing["title"],
                        },
                        "unit_amount": amount_cents,
                    },
                    "quantity": 1,
                }
            ],
            customer_email=buyer_email,
            metadata={
                "order_id": str(order_id),
                "listing_id": str(listing["id"]),
                "seller_id": str(seller_id),
                "buyer_id": str(buyer_id),
            },
            payment_intent_data={
                "application_fee_amount": fee_cents,  # your commission
                "transfer_data": {
                    "destination": seller_stripe_account_id,
                },
            },
            # For now: simple success/cancel URLs.
            # Later you can add a dedicated success page that reads session_id.
            success_url="http://localhost:8501",
            cancel_url="http://localhost:8501",
        )

        # Save Stripe session ID on the order
        update_order_stripe_info(
            order_id=order_id,
            stripe_session_id=session.id,
            stripe_payment_intent_id=None,
        )

        # Clear checkout selection
        st.session_state["checkout_listing_id"] = None

        st.success("✅ Order created. Click below to complete payment on Stripe.")
        st.link_button("Pay securely with Stripe", session.url)

    except Exception as e:
        st.error(f"Error creating Stripe Checkout session: {e}")
        # Optional: revert listing status if you want
        # update_listing_status(seller_id, listing_id, "published")
   