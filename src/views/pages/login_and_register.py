"""Login / Sign-up page: layout and session handling only.
Rules and storage live in AuthController / UserRepository."""
import os

import streamlit as st

from views.components.styles import load_css
from views.session import get_auth_controller, start_session

# NOTE: do NOT call st.set_page_config here. App.py already does it.

load_css("login")


def find_image() -> str | None:
    """Look for the image in views/images, then src/images, then next to this file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))   # .../views/pages
    candidates = [
        os.path.join(base_dir, "..", "images", "LoginAndRegister.png"),
        os.path.join(base_dir, "..", "..", "images", "LoginAndRegister.png"),
        os.path.join(base_dir, "images", "LoginAndRegister.png"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


auth = get_auth_controller()

left_col, right_col = st.columns([5, 4], gap="medium")

with left_col:
    image_path = find_image()
    if image_path:
        st.image(image_path, use_container_width=True)
    else:
        st.warning("Image not found: images/LoginAndRegister.png")

with right_col:
    # Everything lives inside the keyed container so the
    # .st-key-form_panel padding and max-width actually apply.
    with st.container(key="form_panel"):
        st.markdown('<div style="height:20vh"></div>', unsafe_allow_html=True)
        st.markdown('<div class="sh-title">Join StudentHive</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="sh-sub">Login to your verified student account to start exploring.</div>',
            unsafe_allow_html=True,
        )
        st.space("small")

        login_tab, signup_tab = st.tabs(["Login", "Sign-up"])

        # ---------------- LOGIN ----------------
        with login_tab:
            st.write("")
            school_email = st.text_input("School Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            st.space("small")
            login_button = st.button("Login", key="login_btn")
            st.space("small")

            if login_button:
                result = auth.login(school_email, password)
                if result.ok:
                    start_session(result.user)
                    st.rerun()
                else:
                    st.error(result.error)

        # ---------------- SIGN-UP ----------------
        with signup_tab:
            st.write("")
            full_name = st.text_input("Full Name", key="signup_name")
            new_email = st.text_input("School Email", key="signup_email")
            new_password = st.text_input(
                "Password", type="password", key="signup_password"
            )
            confirm_password = st.text_input(
                "Confirm Password", type="password", key="signup_confirm"
            )
            st.space("small")
            signup_button = st.button("Create Account", key="signup_btn")

            st.markdown(
                """
                <div class="sh-legal">
                By creating an account, you agree to our
                <a href="#">Terms of Service</a> and <a href="#">Privacy Policy</a>.
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.space("medium")

            if signup_button:
                result = auth.register(full_name, new_email, new_password, confirm_password)
                if result.ok:
                    # new user -> onboarding from step 1 with empty data
                    start_session(result.user, reset_onboarding=True)
                    st.rerun()
                else:
                    st.error(result.error)
