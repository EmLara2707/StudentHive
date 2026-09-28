import os
import streamlit as st

# set_page_config must be the first Streamlit command
st.set_page_config(page_title="StudentHive", layout="wide")

st.markdown(
    """
    <style>
    /* no page scroll (also removes the scrollbar on the right) */
    html, body,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
        overflow: hidden !important;
    }

    /* remove header, toolbar and colored top bar */
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"] {
        display: none !important;
    }

    /* remove ALL padding around the page, including the left side */
    [data-testid="stMainBlockContainer"],
    .block-container {
        padding: 0 1.5rem 0 0 !important;   /* top right bottom left */
        margin: 0 !important;
        max-width: 100% !important;
    }

    [data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }

    /* image fills the full viewport height and touches the left edge */
    [data-testid="stImage"],
    [data-testid="stImageContainer"] {
        height: 100vh !important;
        width: 100% !important;
        margin: 0 !important;
    }
    [data-testid="stImage"] img {
        height: 100vh !important;
        width: 100% !important;
        object-fit: cover !important;
        border-radius: 0 !important;   /* removes the rounded corners */
        display: block;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

left_col, right_col = st.columns([5, 4], gap="medium")

with left_col:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(BASE_DIR, "images", "LoginAndRegister.png")
    st.image(image_path, use_container_width=True)

with right_col:
    st.write("")
    st.title("Join StudentHive")
    st.header("Create your verified student account to start exploring.", divider="gray")

    login, register = st.tabs(["Login", "Sign-up"])

    with login:
        st.header("Login")
    with register:
        st.header("Register")
