# pag/home.py
import streamlit as st
from core.db import get_all_listings, get_friend_listings


def _format_meta(row):
    bits = []
    if row["brand"]:
        bits.append(str(row["brand"]))
    if row["category"]:
        bits.append(str(row["category"]))
    if row["condition"]:
        bits.append(str(row["condition"]))
    if bits:
        return " · ".join(bits)
    return None


def _listing_card(row, show_seller=True):
    with st.container(border=True):
        col_img, col_text = st.columns([1, 2])

        with col_img:
            if row["image_path"]:
                try:
                    st.image(row["image_path"], width=220)
                except Exception:
                    st.caption("Image not available.")
            else:
                st.caption("No image")

        with col_text:
            st.markdown(f"**{row['title']}** – ${row['price']:.0f}")

            meta = _format_meta(row)
            if meta:
                st.caption(meta)

            if row.get("retail_price"):
                st.caption(f"Original retail: ${row['retail_price']:.0f}")

            st.write(row["description"])

            if show_seller:
                seller = row["seller_name"] or "Unknown"
                st.caption(f"Seller: {seller} • Created: {row['created_at']}")
            else:
                st.caption(f"Created: {row['created_at']}")


def render(user):
    st.header("Circle Marketplace – Home (Friends + All Listings)")

    # ---- Top bar: user + logout/switch ----
    cols = st.columns([3, 1])
    with cols[0]:
        st.markdown(f"Logged in as: **{user.get('email', 'unknown')}**")
    with cols[1]:
        if st.button("Log out / switch user"):
            if "user" in st.session_state:
                del st.session_state["user"]
            st.rerun()

    st.divider()

    # ---- Friends' Listings ----
    st.subheader("Friends' Listings")
    friend_listings = get_friend_listings(user["id"])

    if not friend_listings:
        st.info("No listings from friends yet. Once you add friends, their items will show up here.")
    else:
        for row in friend_listings:
            _listing_card(row, show_seller=True)

    st.divider()

    # ---- All Marketplace Listings ----
    st.subheader("All Marketplace Listings")
    all_listings = get_all_listings()

    if not all_listings:
        st.info("No listings in the marketplace yet. Be the first to create one! ✨")
        return

    for row in all_listings:
        _listing_card(row, show_seller=True)
