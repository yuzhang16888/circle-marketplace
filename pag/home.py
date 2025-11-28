# pag/home.py
import streamlit as st
from core.db import get_all_listings, get_friend_listings


def render(user):
    st.header("Circle Marketplace – Home (Friends + All Listings)")

    # ---- Friends' Listings ----
    st.subheader("Friends' Listings")

    friend_listings = get_friend_listings(user["id"])

    if not friend_listings:
        st.info("No listings from friends yet. Once you add friends, their items will show up here.")
    else:
        for row in friend_listings:
            with st.container(border=True):
                st.markdown(f"**{row['title']}** – ${row['price']:.0f}")
                st.write(row["description"])
                if row["image_path"]:
                    try:
                        st.image(row["image_path"], use_container_width=True)
                    except Exception:
                        st.caption("Image not available.")
                st.caption(f"Seller: {row['seller_name']} • Created: {row['created_at']}")

    st.divider()

    # ---- All Marketplace Listings ----
    st.subheader("All Marketplace Listings")

    all_listings = get_all_listings()

    if not all_listings:
        st.info("No listings in the marketplace yet. Be the first to create one! ✨")
        return

    for row in all_listings:
        with st.container(border=True):
            st.markdown(f"**{row['title']}** – ${row['price']:.0f}")
            st.write(row["description"])
            if row["image_path"]:
                try:
                    st.image(row["image_path"], use_container_width=True)
                except Exception:
                    st.caption("Image not available.")
            # If seller_name is missing for some older rows, fall back gracefully
            seller = row.get("seller_name") if isinstance(row, dict) else row["seller_name"]
            st.caption(f"Seller: {seller or 'Unknown'} • Created: {row['created_at']}")
