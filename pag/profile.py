
# pag/profile.py
from typing import Optional

import streamlit as st
# import stripe

from core.auth import get_current_user, logout
from core import api_client
from core.db import get_user_by_id, update_user_stripe_account


def render(user: Optional[dict] = None):
    """
    Profile & Friends page.
    Shows basic account info, Stripe payouts setup, invites, and logout.
    """
    if user is None:
        user = get_current_user()

    if not user:
        st.error("You need to be logged in to see your profile.")
        st.stop()

    st.header("Profile & Friends")

    # -------------------
    # Basic account info
    # -------------------
    st.subheader("Your account")

    st.write(f"**Email:** {user.get('email', '')}")
    full_name = user.get("full_name") or "Not set"
    st.write(f"**Name:** {full_name}")
    st.write(f"**User ID:** {user.get('id', '—')}")

    # -------------------
    # Stripe payouts
    # -------------------
    # st.markdown("---")
    # st.subheader("Stripe payouts")

    # user_id = user["id"]
    # user_row = get_user_by_id(user_id)

    # stripe_account_id = None
    # stripe_onboarded = False
    # if user_row:
    #     stripe_account_id = user_row["stripe_account_id"]
    #     stripe_onboarded = bool(user_row["stripe_onboarded"])

    # if stripe_account_id:
    #     st.success(f"Stripe account connected: `{stripe_account_id}`")
    #     st.caption(
    #         "Status: " + ("Onboarded ✔️" if stripe_onboarded else "Onboarding in progress…")
    #     )
    # else:
    #     st.info(
    #         "You haven't connected a Stripe account yet. "
    #         "Connect Stripe to receive payouts when you sell items on Circle."
    #     )

    # if st.button("Connect / manage Stripe payouts"):
    #     try:
    #         stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

    #         # If no account yet, create one (similar to pag/test_strip_connect.py)
    #         if not stripe_account_id:
    #             account = stripe.Account.create(
    #                 type="standard",
    #                 email=user.get("email"),
    #                 capabilities={
    #                     "card_payments": {"requested": True},
    #                     "transfers": {"requested": True},
    #                 },
    #                 metadata={"circle_user_id": str(user_id)},
    #             )

    #             update_user_stripe_account(
    #                 user_id=user_id,
    #                 stripe_account_id=account.id,
    #                 onboarded=False,
    #             )
    #             stripe_account_id = account.id
    #             st.success(
    #                 f"✅ Created Stripe account `{account.id}` and saved it to your profile."
    #             )

    #         # Generate an onboarding / update link
    #         account_link = stripe.AccountLink.create(
    #             account=stripe_account_id,
    #             refresh_url="http://localhost:8501/profile",  # adjust if profile path differs
    #             return_url="http://localhost:8501/profile",
    #             type="account_onboarding",
    #         )

    #         st.write("Open Stripe onboarding in a new tab:")
    #         st.markdown(f"[Open Stripe onboarding]({account_link['url']})")

    #     except Exception as e:
    #         st.error(f"Error talking to Stripe: {e}")

    # -------------------
    # Sign out
    # -------------------
    st.markdown("---")
    st.subheader("Sign out")

    if st.button("Log out"):
        logout()
        st.success("You have been logged out.")
        st.rerun()

    # -------------------
    # Invites
    # -------------------
    st.markdown("---")
    st.subheader("Invite friends to Circle")

    with st.form("profile_invite_form"):
        friend_name = st.text_input("Friend's name", key="prof_invite_name")
        friend_email = st.text_input("Friend's email", key="prof_invite_email")
        submitted = st.form_submit_button("Send invite")

    if submitted:
        if not friend_email:
            st.error("Please enter your friend's email.")
        else:
            try:
                api_client.create_invite(
                    email=friend_email,
                    name=friend_name,
                    invited_by_id=user["id"],
                )
                st.success(f"Invitation sent to {friend_email}.")
            except Exception as e:
                st.error(f"Failed to send invite: {e}")

    st.subheader("People you've invited")

    try:
        data = api_client.list_invites_by_inviter(user["id"])
        invites = data.get("invites", [])
        if not invites:
            st.info("You haven't invited anyone yet.")
        else:
            rows = []
            for inv in invites:
                status = "Joined" if inv.get("used_by_user_id") else "Pending"
                rows.append(
                    {
                        "Email": inv.get("email"),
                        "Status": status,
                        "Invited at": inv.get("created_at"),
                    }
                )
            st.table(rows)
    except Exception as e:
        st.error(f"Could not load your invites: {e}")



####Archive ##########
# # pag/profile.py
# import streamlit as st
# from typing import Optional
# from core.auth import get_current_user, logout
# from core import api_client
# import stripe
# from core.db import get_user_by_id, update_user_stripe_account


# def render(user: Optional[dict] = None):
#     """
#     Profile & Friends page.
#     For now: show basic account info and a logout button.
#     Later: we can add change-password and friends/referrals.
#     """
#     if user is None:
#         user = get_current_user()

#     if not user:
#         st.error("You need to be logged in to see your profile.")
#         st.stop()

#     st.header("Profile & Friends")

#     st.subheader("Your account")

#     st.write(f"**Email:** {user.get('email', '')}")
#     full_name = user.get("full_name") or "Not set"
#     st.write(f"**Name:** {full_name}")
#     st.write(f"**User ID:** {user.get('id', '—')}")

#     st.markdown("---")

#     st.subheader("Sign out")

#     if st.button("Log out"):
#         logout()
#         st.success("You have been logged out.")
#         st.rerun()
     
#     #st.markdown("---")
#     #st.caption("More profile and friend features coming soon ✨")
#         st.markdown("---")
#     st.subheader("Invite friends to Circle")

#     with st.form("profile_invite_form"):
#         friend_name = st.text_input("Friend's name", key="prof_invite_name")
#         friend_email = st.text_input("Friend's email", key="prof_invite_email")
#         submitted = st.form_submit_button("Send invite")

#     if submitted:
#         if not friend_email:
#             st.error("Please enter your friend's email.")
#         else:
#             try:
#                 api_client.create_invite(
#                     email=friend_email,
#                     name=friend_name,
#                     invited_by_id=user["id"],
#                 )
#                 st.success(f"Invitation sent to {friend_email}.")
#             except Exception as e:
#                 st.error(f"Failed to send invite: {e}")

#     st.subheader("People you've invited")

#     try:
#         data = api_client.list_invites_by_inviter(user["id"])
#         invites = data.get("invites", [])
#         if not invites:
#             st.info("You haven't invited anyone yet.")
#         else:
#             rows = []
#             for inv in invites:
#                 status = "Joined" if inv.get("used_by_user_id") else "Pending"
#                 rows.append(
#                     {
#                         "Email": inv.get("email"),
#                         "Status": status,
#                         "Invited at": inv.get("created_at"),
#                     }
#                 )
#             st.table(rows)
#     except Exception as e:
#         st.error(f"Could not load your invites: {e}")

