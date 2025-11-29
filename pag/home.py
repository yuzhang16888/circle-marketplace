# pag/home.py
import streamlit as st
from core.db import get_all_listings, get_friend_listings


def render(user):
    st.header("Circle Marketplace – Home (Friends + All Listings)")

    # ---- Top bar: user + logout/switch ----
    cols = st.columns([3, 1])
    with cols[0]:
        st.markdown(f"Logged in as: **{user.get('email', 'unknown')}**")
    with cols[1]:
        if st.button("Log out / switch user"):
            # Clear current user and rerun → will show login screen again
            if "user" in st.session_state:
                del st.session_state["user"]
            st.rerun()  # ✅ use st.rerun() in modern Streamlit

    st.divider()

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
                seller = row["seller_name"] or "Unknown"
                st.caption(f"Seller: {seller} • Created: {row['created_at']}")

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
            seller = row["seller_name"] or "Unknown"
            st.caption(f"Seller: {seller} • Created: {row['created_at']}")
