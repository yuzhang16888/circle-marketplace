# pag/my_listings.py
import streamlit as st
from core.db import get_listings_for_user

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
