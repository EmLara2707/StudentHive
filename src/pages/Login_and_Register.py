import streamlit as st;
import os

st.set_page_config(page_title="StudentHive", layout="wide")

col1, col2 = st.columns(2, gap="xxlarge", width="stretch")

with col1:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(BASE_DIR, "images", "LoginAndRegister.png")
    st.image(image_path, width="stretch")

with col2:
    st.title("Join StudentHive")

