# pages/create_listing.py
import streamlit as st
from core.db import insert_listing
from core.storage import save_listing_image

def render(user):
    st.header("Create a New Listing")

    with st.form("create_listing_form", clear_on_submit=False):
        title = st.text_input("Title")
        description = st.text_area("Description")
        price = st.number_input("Price", min_value=0.0, step=1.0)
        image_file = st.file_uploader("Upload images", type=["jpg", "jpeg", "png"])

        submitted = st.form_submit_button("Publish Listing")

    if submitted:
        if not title or not description:
            st.error("Title and description are required.")
            return

        image_path = None
        if image_file is not None:
            image_path = save_listing_image(user["id"], image_file)

        listing_id = insert_listing(
            user_id=user["id"],
            title=title,
            description=description,
            price=price,
            image_path=image_path,
        )

        st.success("Listing published!")
        st.write(f"Listing ID: {listing_id}")
