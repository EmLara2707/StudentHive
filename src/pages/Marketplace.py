import streamlit as st

st.set_page_config(page_title="StudentHive", layout="wide")

st.title("Marketplace")
st.subheader("Browse offered services and item rentals across your campus!")
st.space("xxsmall")
st.divider()

col1, col2, col3 = st.columns(3, vertical_alignment="center", border=True, width="stretch")

with col1:
    st.write("Test1")
with col2:
    st.write("Test2")
with col3:
    st.write("Test3")