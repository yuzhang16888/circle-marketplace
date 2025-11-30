# pag/admin_dashboard.py
import streamlit as st
from core.db import get_all_users, get_friend_ids, add_friend
from core import api_client

def render(user):
    st.header("Admin Dashboard – Friend Manager")

    st.markdown(
        f"Current user: **{user['email']}** (id: `{user['id']}`)"
    )

    st.divider()
    col_left, col_right = st.columns([3, 2])
    # ----- Load users & friends -----
    all_users = get_all_users()
    friend_ids = set(get_friend_ids(user["id"]))

    # Separate current user vs others
    other_users = [u for u in all_users if u["id"] != user["id"]]

    col_left, col_right = st.columns(2)




def render(user):
    st.header("Admin Dashboard")

    # ... your existing admin UI (orders, listings, etc.) ...

    st.subheader("Invite a friend to Circle")

    invite_email = st.text_input("Friend's email", key="invite_email")

    if st.button("Create invite", key="invite_button"):
        if not invite_email:
            st.error("Please enter an email.")
        else:
            try:
                resp = api_client.create_invite(invite_email, invited_by_id=user["id"])
                st.success(f"Invite created for {invite_email} (ID: {resp['invite_id']}).")
            except Exception as e:
                st.error(f"Failed to create invite: {e}")

    # Optional: show recent invites
    if st.checkbox("Show all invites", key="show_invites"):
        try:
            data = api_client.list_invites()
            invites = data.get("invites", [])
            if not invites:
                st.info("No invites yet.")
            else:
                st.table(invites)
        except Exception as e:
            st.error(f"Failed to load invites: {e}")


    # ----- LEFT: all users (add as friend) -----
    with col_left:
        st.subheader("All Users")

        if not other_users:
            st.info("There are no other users yet. Log in with another email to create more users.")
        else:
            for u in other_users:
                is_friend = u["id"] in friend_ids
                label = u["display_name"] or u["email"]

                cols = st.columns([3, 1])
                with cols[0]:
                    st.markdown(f"**{label}**  \n`{u['email']}`  \n(id: `{u['id']}`)")

                with cols[1]:
                    if is_friend:
                        st.button("✅ Friend", key=f"friend_{u['id']}", disabled=True)
                    else:
                        if st.button("Add friend", key=f"add_{u['id']}"):
                            add_friend(user["id"], u["id"])
                            st.success(f"Added {label} as a friend.")
                            st.experimental_rerun()

    # ----- RIGHT: current friends -----
    with col_right:
        st.subheader("Your Friends")

        if not friend_ids:
            st.info("You don't have any friends set yet. Add some from the left side.")
        else:
            friend_map = {u["id"]: u for u in all_users if u["id"] in friend_ids}
            for fid, fu in friend_map.items():
                label = fu["display_name"] or fu["email"]
                st.markdown(f"• **{label}**  \n`{fu['email']}`  \n(id: `{fid}`)")
