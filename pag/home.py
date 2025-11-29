# pag/home.py
import json
import streamlit as st
from core.db import get_all_listings, get_friend_listings


def _format_meta(row):
    bits = []
    if row["brand"]:
        bits.append(str(row["brand"]))
    if row["category"]:
        bits.append(str(row["category"]))
    if row["condition"]:
        bits.append(str(row["condition"]))
    return " · ".join(bits) if bits else None


def _get_image_list(row):
    """Return a list of image paths for this listing."""
    paths = []

    if row["image_paths"]:
        try:
            loaded = json.loads(row["image_paths"])
            if isinstance(loaded, list):
                paths = [p for p in loaded if p]
        except Exception:
            paths = []

    # Fallback to single image_path if needed
    if not paths and row["image_path"]:
        paths = [row["image_path"]]

    return paths


def _listing_card(row, user, prefix: str):
    listing_id = row["id"]
    img_key = f"{prefix}_img_idx_{listing_id}"

    # Initialize carousel index
    if img_key not in st.session_state:
        st.session_state[img_key] = 0

    image_paths = _get_image_list(row)
    num_images = len(image_paths)

    # Initialize cart and likes in session
    if "cart_listing_ids" not in st.session_state:
        st.session_state["cart_listing_ids"] = []
    if "liked_listing_ids" not in st.session_state:
        st.session_state["liked_listing_ids"] = []

    cart_ids = st.session_state["cart_listing_ids"]
    liked_ids = st.session_state["liked_listing_ids"]

    in_cart = listing_id in cart_ids
    liked = listing_id in liked_ids

    with st.container(border=True):
        col_img, col_text = st.columns([1, 2])

        # ---------- IMAGE + CAROUSEL ----------
        with col_img:
            if image_paths:
                idx = st.session_state[img_key] % num_images
                current_path = image_paths[idx]

                try:
                    st.image(current_path, width=220)
                except Exception:
                    st.caption("Image not available.")

                if num_images > 1:
                    c1, c2, c3 = st.columns([1, 1, 1])
                    with c1:
                        if st.button("◀", key=f"{prefix}_prev_{listing_id}"):
                            st.session_state[img_key] = (idx - 1) % num_images
                            st.experimental_rerun()
                    with c2:
                        st.caption(f"{idx + 1} / {num_images}")
                    with c3:
                        if st.button("▶", key=f"{prefix}_next_{listing_id}"):
                            st.session_state[img_key] = (idx + 1) % num_images
                            st.experimental_rerun()
            else:
                st.caption("No image")

        # ---------- TEXT + META + ACTIONS ----------
        with col_text:
            st.markdown(f"**{row['title']}** – ${float(row['price']):.0f}")

            meta = _format_meta(row)
            if meta:
                st.caption(meta)

            if row["retail_price"] is not None:
                st.caption(f"Original retail: ${float(row['retail_price']):.0f}")

            st.write(row["description"])

            seller = row["seller_name"] if row["seller_name"] else "Unknown"
            st.caption(f"Seller: {seller} • Created: {row['created_at']}")

            # --- ACTIONS: LIKE + ADD TO CART ---
            col_like, col_cart = st.columns(2)

            with col_like:
                like_label = "❤️ Liked" if liked else "🤍 Like"
                if st.button(like_label, key=f"{prefix}_like_{listing_id}"):
                    if liked:
                        st.session_state["liked_listing_ids"] = [
                            x for x in liked_ids if x != listing_id
                        ]
                    else:
                        st.session_state["liked_listing_ids"] = liked_ids + [listing_id]
                    st.experimental_rerun()

            with col_cart:
                cart_label = "Remove from cart" if in_cart else "Add to cart"
                if st.button(cart_label, key=f"{prefix}_cart_{listing_id}"):
                    if in_cart:
                        st.session_state["cart_listing_ids"] = [
                            x for x in cart_ids if x != listing_id
                        ]
                    else:
                        st.session_state["cart_listing_ids"] = cart_ids + [listing_id]
                    st.experimental_rerun()


def render(user):
    st.header("Circle Marketplace – Home (Friends + All Listings)")

    # ---- Top bar: user + logout/switch + quick cart/likes summary ----
    cols = st.columns([3, 2, 1])
    with cols[0]:
        st.markdown(f"Logged in as: **{user.get('email', 'unknown')}**")

    # Ensure session state keys exist
    if "cart_listing_ids" not in st.session_state:
        st.session_state["cart_listing_ids"] = []
    if "liked_listing_ids" not in st.session_state:
        st.session_state["liked_listing_ids"] = []

    with cols[1]:
        cart_count = len(st.session_state["cart_listing_ids"])
        like_count = len(st.session_state["liked_listing_ids"])
        st.caption(f"🛒 Cart: {cart_count} • ❤️ Liked: {like_count}")

    with cols[2]:
        if st.button("Log out / switch user"):
            if "user" in st.session_state:
                del st.session_state["user"]
            st.rerun()

    st.divider()

    # ---- Friends' Listings ----
    st.subheader("Friends' Listings")
    friend_listings = get_friend_listings(user["id"])

    if not friend_listings:
        st.info("No listings from friends yet. Once you add friends, their items will show up here.")
    else:
        for row in friend_listings:
            _listing_card(row, user, prefix="friend")

    st.divider()

    # ---- All Marketplace Listings ----
    st.subheader("All Marketplace Listings")
    all_listings = get_all_listings()

    if not all_listings:
        st.info("No listings in the marketplace yet. Be the first to create one! ✨")
        return

    for row in all_listings:
        _listing_card(row, user, prefix="all")
