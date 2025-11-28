# pag/home.py
import streamlit as st
from core.db import get_all_listings, get_friend_listings

def render(user):
    st.header("Circle Marketplace – Home")

    # ---- Friends Listings ----
    st.subheader("Friends' Listings")
    friend_listings = get_friend_listings(user["id"])

    if not friend_listings:
        st.info("No listings from friends yet.")
    else:
        for row in friend_listings:
            with st.container(border=True):
                st.markdown(f"**{row['title']}** – ${row['price']:.0f}")
                st.write(row["description"])
                if row["image_path"]:
                    st.image(row["image_path"], use_container_width=True)
                st.caption(f"Seller: {row['seller_name']} • Created: {row['created_at']}")

    st.divider()

    # ---- All Listings ----
    st.subheader("All Marketplace Listings")
    all_listings = get_all_listings()

    if not all_listings:
        st.info("No listings yet. Be the first to create one!")
        return

    for row in all_listings:
        with st.container(border=True):
            st.markdown(f"**{row['title']}** – ${row['price']:.0f}")
            st.write(row["description"])
            if row["image_path"]:
                st.image(row["image_path"], use_container_width=True)
            st.caption(f"Seller: {row['seller_name']} • Created: {row['created_at']}")
