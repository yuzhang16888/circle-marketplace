# pag/admin_dashboard.py
import streamlit as st
from cor.db import get_all_listings

def render(user):
    st.header("Admin Dashboard")

    # later you can add permission logic here
    listings = get_all_listings()

    st.write(f"Total listings: {len(listings)}")

    for row in listings:
        with st.container(border=True):
            st.markdown(f"**{row['title']}** – ${row['price']:.0f}")
            st.write(row["description"])
            st.caption(f"User: {row['user_id']} • ID: {row['id']} • {row['created_at']}")
