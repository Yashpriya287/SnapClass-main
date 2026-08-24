import streamlit as st

def footer_home():
    st.markdown(f"""
    <div style=" margin-top:2rem; display:flex; align-items:center; gap:6px; justify-content:center">
    <p style="font-weight:bold; color:white">Created with ❤️ by Yashpriya </p>
    </div>


""", unsafe_allow_html=True)

def footer_dashboard():
    st.markdown(f"""
    <div style=" margin-top:2rem; display:flex; align-items:center; gap:6px; justify-content:center">
    <p style="font-weight:bold; color:black">Created with ❤️ by Yashpriya </p>
    </div>


""", unsafe_allow_html=True)    