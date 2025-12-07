# pag/create_listing.py
import streamlit as st
from core.db import insert_listing
from core.storage import save_listing_image


CATEGORIES = [
    "Bags",
    "Shoes",
    "Clothing",
    "Jewelry",
    "Accessories",
    "Home",
    "Beauty",
    "Electronics",
    "Art",
    "Other",
]

CONDITIONS = [
    "New (with tags)",
    "New (no tags)",
    "Like new",
    "Gently used",
    "Well-loved",
    "Vintage",
    "Other",
]


def render(user):
    st.header("Create a Listing")

    st.markdown(
        "Share a piece from your circle. "
        "Thoughtful details help buyers feel confident about condition and value."
    )

    title = st.text_input("Title *")
    brand = st.text_input("Brand", help="Maximum 30 words.e.g., Chanel, Pokemon, Celine, Loewe, etc.")
    category = st.selectbox("Category *", CATEGORIES, index=0)
    if category == "Other":
        category_other = st.text_input("Category (custom)")
    else:
        category_other = None

    condition = st.selectbox("Condition *", CONDITIONS, index=2)
    if condition == "Other":
        condition_other = st.text_input("Condition (custom)")
    else:
        condition_other = None

    col1, col2 = st.columns(2)
    with col1:
        retail_price = st.number_input(
            "Original retail price($)",
            min_value=0,
            step=10,
            format="%d",
            help="If known. Helps buyers understand the value.",
        )
    with col2:
        price = st.number_input(
            "Your listing price($) *",
            min_value=0,
            step=10,
            format="%d",
        )

    description = st.text_area(
        "Description *",
        help="Include sizing info, flaws, how often used, and anything that builds trust.(Maximum 300 words.)",
    )

    st.markdown("**Photos (up to 7)**")
    uploaded_files = st.file_uploader(
        "Upload clear photos (front, back, details)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        st.caption("Preview of your photos:")
        st.image(uploaded_files[:7], width=160)

    st.caption("Fields marked with * are required.")

    col_pub, col_draft = st.columns(2)
    with col_pub:
        publish_clicked = st.button("Publish Listing", use_container_width=True)
    with col_draft:
        draft_clicked = st.button("Save as draft", use_container_width=True)

    if not (publish_clicked or draft_clicked):
        return

    # Which action?
    status = "published" if publish_clicked else "draft"

    # Basic validation
    errors = []
    if not title.strip():
        errors.append("Title is required.")
    else:
        title_word_count = len(title.split())
        if title_word_count > 30:
             errors.append(
                f"Title is too long ({title_word_count} words). Please keep it within 30 words."
        )

    if not description.strip():
        errors.append("Description is required.")
    else:
        desc_word_count = len(description.split())
        if desc_word_count > 300:
            errors.append(
                f"Description is too long ({desc_word_count} words). Please keep it within 300 words."
            )
            
        
    if price <= 0:
        errors.append("Listing price must be greater than 0.")

    if category == "Other":
        if not category_other or not category_other.strip():
            errors.append("Please specify a custom category.")
        final_category = category_other.strip()
    else:
        final_category = category

    if condition == "Other":
        if not condition_other or not condition_other.strip():
            errors.append("Please specify a custom condition.")
        final_condition = condition_other.strip()
    else:
        final_condition = condition

    if errors:
        for e in errors:
            st.error(e)
        return

    # Save images (limit to 7)
    image_paths = []
    if uploaded_files:
        for f in uploaded_files[:7]:
            path = save_listing_image(user_id=user["id"], file=f)
            image_paths.append(path)

    # If retail price is 0, store it as None so DB isn't cluttered
    retail_value = retail_price if retail_price > 0 else None

        listing_id = insert_listing(
        user_id=user["id"],
        title=title.strip(),
        description=description.strip(),
        price=price,
        brand=brand.strip() or None,
        category=final_category,
        condition=final_condition,
        retail_price=retail_value,
        image_paths=image_paths,
        status=status,
    )

    if status == "published":
        st.success(
            f"Your listing has been published. 🎉 "
            f"You can view your listing on the Home page now."
        )

        # Allow user to immediately create another listing
        if st.button("Create another listing"):
            st.rerun()
    else:
        st.success(
            "Your listing has been saved as a draft. "
            "You can manage it from **My Listings**."
        )

    st.info(f"(Listing ID: {listing_id})")
