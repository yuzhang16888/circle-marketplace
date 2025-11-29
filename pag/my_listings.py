# pag/my_listings.py
import streamlit as st
from core.db import get_listings_for_user


def render(user):
    st.header("My Listings")

    rows = get_listings_for_user(user["id"])

    if not rows:
        st.info("You haven't created any listings yet. Start by creating one!")
        return

    for row in rows:
        with st.container(border=True):
            status = row["status"] or "published"
            status_label = "✅ Published" if status == "published" else "📝 Draft"
            st.markdown(f"**{row['title']}** – ${row['price']:.0f} &nbsp;&nbsp; _{status_label}_")

            meta_bits = []
            if row["brand"]:
                meta_bits.append(str(row["brand"]))
            if row["category"]:
                meta_bits.append(str(row["category"]))
            if row["condition"]:
                meta_bits.append(str(row["condition"]))
            if meta_bits:
                st.caption(" · ".join(meta_bits))

            if row["retail_price"]:
                st.caption(f"Original retail: ${row['retail_price']:.0f}")

            st.write(row["description"])

            if row["image_path"]:
                try:
                    st.image(row["image_path"], use_container_width=True)
                except Exception:
                    st.caption("Image not available.")

            st.caption(f"Created: {row['created_at']} (Listing ID: {row['id']})")

            # Future: add buttons to edit / delete / publish draft, etc.
