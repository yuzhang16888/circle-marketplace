# pag/my_listings.py
import streamlit as st
from core.db import get_listings_for_user, delete_listing, update_listing_status


def render(user):
    st.header("My Listings")

    rows = get_listings_for_user(user["id"])

    if not rows:
        st.info("You haven't created any listings yet. Start by creating one!")
        return

    for row in rows:
        status = row["status"] or "published"
        status_label = {
            "published": "✅ Published",
            "draft": "📝 Draft",
            "inactive": "⏸ Deactivated",
        }.get(status, status)

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
                st.caption(f"Created: {row['created_at']} (Listing ID: {row['id']})")

                # --- Actions ---
                col1, col2, col3 = st.columns(3)

                # Delete
                with col1:
                    if st.button("Delete Listing", key=f"delete_{row['id']}"):
                        success = delete_listing(user["id"], row["id"])
                        if success:
                            st.success("Listing deleted.")
                            st.experimental_rerun()
                        else:
                            st.error("Could not delete listing. Please try again.")

                # Deactivate / Reactivate
                with col2:
                    if status == "published":
                        label = "Deactivate Listing"
                        new_status = "inactive"
                    elif status == "inactive":
                        label = "Reactivate Listing"
                        new_status = "published"
                    else:
                        label = None
                        new_status = None

                    if label:
                        if st.button(label, key=f"status_{row['id']}"):
                            ok = update_listing_status(user["id"], row["id"], new_status)
                            if ok:
                                msg = "Listing deactivated." if new_status == "inactive" else "Listing reactivated and visible on Home."
                                st.success(msg)
                                st.experimental_rerun()
                            else:
                                st.error("Could not update listing status. Please try again.")

                # Optional: future "Publish Draft" button
                with col3:
                    if status == "draft":
                        if st.button("Publish Draft", key=f"publish_{row['id']}"):
                            ok = update_listing_status(user["id"], row["id"], "published")
                            if ok:
                                st.success("Draft published and now visible on Home.")
                                st.experimental_rerun()
                            else:
                                st.error("Could not publish draft. Please try again.")
