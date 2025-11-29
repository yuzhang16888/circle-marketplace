# pag/cart.py
import json
import streamlit as st
from core.db import get_listings_by_ids


def _format_meta(row):
    bits = []
    if row["brand"]:
        bits.append(str(row["brand"]))
    if row["category"]:
        bits.append(str(row["category"]))
    if row["condition"]:
        bits.append(str(row["condition"]))
    return " · ".join(bits) if bits else None


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
    st.header("My Cart")

    # Ensure cart state exists
    if "cart_listing_ids" not in st.session_state:
        st.session_state["cart_listing_ids"] = []

    cart_ids = st.session_state["cart_listing_ids"]

    if not cart_ids:
        st.info("Your cart is empty. Add items from the Home page to see them here. 🛒")
        return

    # Use unique IDs but preserve order
    unique_ids = list(dict.fromkeys(cart_ids))

    rows = get_listings_by_ids(unique_ids)
    if not rows:
        st.info("No valid items found for your cart yet.")
        return

    st.caption(f"You currently have {len(unique_ids)} item(s) in your cart.")

    subtotal = 0.0

    for row in rows:
        price = float(row["price"])
        subtotal += price

        listing_id = row["id"]
        image_paths = _get_image_list(row)

        with st.container(border=True):
            col_img, col_text = st.columns([1, 2])

            with col_img:
                if image_paths:
                    try:
                        st.image(image_paths[0], width=200)
                    except Exception:
                        st.caption("Image not available.")
                else:
                    st.caption("No image")

            with col_text:
                st.markdown(f"**{row['title']}** – ${price:.0f}")

                meta = _format_meta(row)
                if meta:
                    st.caption(meta)

                if row["retail_price"] is not None:
                    st.caption(f"Original retail: ${float(row['retail_price']):.0f}")

                st.write(row["description"])

                seller = row["seller_name"] if row["seller_name"] else "Unknown"
                st.caption(f"Seller: {seller}")

                # Remove from cart
                if st.button("Remove from cart", key=f"remove_cart_{listing_id}"):
                    st.session_state["cart_listing_ids"] = [
                        x for x in st.session_state["cart_listing_ids"] if x != listing_id
                    ]
                    st.rerun()

    st.divider()

    st.subheader("Order Summary")
    st.markdown(f"**Subtotal:** ${subtotal:.0f}")
    st.caption("Taxes, shipping, and payment are not handled in this MVP yet.")

    # Simple checkout stub
    if st.button("Proceed to Checkout (MVP)"):
        st.success(
            "Checkout flow is coming soon. For now, screenshot or copy this page and "
            "reach out to the seller(s) directly using your usual channels."
        )

        st.info(
            "Future version: we'll handle secure payments, shipping options, and "
            "in-app messaging between buyers and sellers."
        )
