# pages/home.py
import streamlit as st

def render(user):
    st.header("Circle Marketplace – Home")
    st.write("✅ `pages.home.render()` is working.")
    if user:
        st.write(f"Logged in as: **{user.get('email', 'unknown')}**")
