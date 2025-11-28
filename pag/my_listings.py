# pag/my_listings.py
import streamlit as st
from core.db import get_listings_for_user
from core.db import init_db, insert_listing, get_listings_for_user, get_all_listings
from core.storage import save_listing_image
from core.auth import ensure_user_logged_in

def render(user):
    st.header("My Listings")

    rows = get_listings_for_user(user["id"])

    if not rows:
        st.info("You have no listings yet. Try creating one! ✨")
        return

    for row in rows:
        with st.container(border=True):
            st.markdown(f"**{row['title']}** – ${row['price']:.0f}")
            st.write(row["description"])
            if row["image_path"]:
                try:
                    st.image(row["image_path"], use_container_width=True)
                except Exception:
                    st.caption("Image not available.")
            st.caption(f"ID: {row['id']} • Created at: {row['created_at']}")
