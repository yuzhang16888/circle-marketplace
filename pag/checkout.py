# pag/checkout.py
import json
import streamlit as st
from core.db import (
    get_listings_by_ids,
    create_order,
    update_listing_status,
)
# update_listing_status already exists in your db file


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
            state = st.selectbox("Province / Territory", CA_PROVINCES, index=CA_PROVINCES.index("ON"))

        postal_code = st.text_input("ZIP / Postal code", value="")

        phone_raw = st.text_input(
            "Mobile phone",
            value="",
            placeholder="e.g. (415) 555-1234",
        )

        st.subheader("Payment preference (off-platform for now)")
        payment_method = st.selectbox(
            "Preferred payment method",
            ["Venmo", "PayPal", "Zelle", "Cash App", "Bank transfer", "Other"],
        )

        buyer_note = st.text_area(
            "Notes for the seller (optional)",
            placeholder="e.g. Please ship with signature required.",
        )

        submitted = st.form_submit_button("Place order")

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
        # Simple check: 6 characters (A1A1A1 style). We keep it len-based for MVP.
        if len(postal_code_clean) != 6:
            errors.append("For Canada, postal code should be 6 characters (e.g., A1A1A1).")

    # Phone normalization: US/Canada 10 digits
    digits = "".join(ch for ch in phone_raw if ch.isdigit())
    if len(digits) != 10:
        errors.append("Please enter a valid 10-digit phone number for US/Canada.")
        formatted_phone = phone_raw.strip()
    else:
        formatted_phone = f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"

    if errors:
        for e in errors:
            st.error(e)
        return

    # ---------- CREATE ORDER ----------
# ---------- CREATE ORDER ----------
buyer_id = user["id"]
total_price = price  # no fees yet in MVP

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
    payment_method=payment_method,
    buyer_note=buyer_note.strip(),
)

# Mark listing as reserved so it disappears from public feed
update_listing_status(listing_id, "reserved")

# Remove from cart
if "cart_listing_ids" in st.session_state:
    st.session_state["cart_listing_ids"] = [
        x for x in st.session_state["cart_listing_ids"] if x != listing_id
    ]

# Clear checkout selection
st.session_state["checkout_listing_id"] = None

# ------------------ SUCCESS MESSAGES ------------------
st.success("🎉 Order placed successfully!")
st.info("We will email you as soon as the seller ships your item.")

# Optionally redirect them home after confirmation
if st.button("Return to Home"):
    st.session_state["main_nav"] = "Home"
    st.rerun()
