"""Login / Sign-up page: layout and session handling only.
Rules and storage live in AuthController / UserRepository."""
import os

import streamlit as st

from views.components.auth_cookie import queue_cookie_write
from views.components.legal import privacy_dialog, terms_dialog
from views.components.session_lifecycle import pop_session_notice
from views.components.styles import load_css
from views.session import get_auth_controller, start_session, store_auth_tokens

# NOTE: do NOT call st.set_page_config here. App.py already does it.

load_css("login")


_PENDING_KEY = "pending_confirm_email"      # the address waiting for its 6-digit code


def _confirm_panel(auth) -> None:
    """Enter the code from the confirmation email. Replaces the Login / Sign-up tabs after
    sign-up, or after a login refused because the email isn't confirmed yet."""
    email = st.session_state[_PENDING_KEY]
    st.markdown('<div class="sh-title" style="font-size:1.6rem">Confirm your email</div>',
                unsafe_allow_html=True)
    st.info(f"We sent a 6-digit code to **{email}**. Check your inbox and your junk folder.")
    code = st.text_input("Confirmation code", key="confirm_code", max_chars=12,
                         placeholder="123456")
    with st.container(horizontal=True, horizontal_alignment="distribute", key="confirm_nav"):
        back = st.button("Back", key="confirm_back")             # return to Login / Sign-up
        verify = st.button("Confirm account", key="confirm_btn")
    with st.container(horizontal=True, horizontal_alignment="center", key="confirm_row"):
        resend = st.button("Send a new code", key="confirm_resend", type="tertiary")

    if back:
        st.session_state.pop(_PENDING_KEY, None)
        st.session_state.pop("confirm_code", None)
        st.rerun()
    if resend:
        result = auth.resend_code(email)
        if result.ok:
            st.success("A new code is on its way. Check your inbox and junk folder.")
        else:
            st.error(result.error)
    if verify:
        result = auth.confirm_signup(email, code)
        if result.ok:
            st.session_state.pop(_PENDING_KEY, None)
            st.session_state.pop("confirm_code", None)
            if result.tokens:
                store_auth_tokens(*result.tokens)
                queue_cookie_write(result.tokens[1])        # survive a page refresh
            start_session(result.user, reset_onboarding=True)   # new account: onboarding
            st.rerun()
        else:
            st.error(result.error)


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

        notice = pop_session_notice()           # e.g. "Your session expired..."
        if notice:
            st.warning(notice)

        if st.session_state.get(_PENDING_KEY):      # waiting for the emailed code
            _confirm_panel(auth)
            st.stop()

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
                    if result.tokens:
                        store_auth_tokens(*result.tokens)
                        queue_cookie_write(result.tokens[1])    # survive a page refresh
                    start_session(result.user)
                    st.rerun()
                elif result.needs_confirmation:     # account exists, email not confirmed
                    st.session_state[_PENDING_KEY] = school_email.strip().lower()
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

            with st.container(horizontal=True, horizontal_alignment="center",
                              vertical_alignment="center", gap="xxsmall", key="legal_links"):
                st.markdown('<span class="sh-legal-text">By creating an account, you agree to our</span>',
                            unsafe_allow_html=True)
                if st.button("Terms of Service", key="terms_link"):
                    terms_dialog()
                st.markdown('<span class="sh-legal-text">and</span>', unsafe_allow_html=True)
                if st.button("Privacy Policy", key="privacy_link"):
                    privacy_dialog()
            st.space("medium")

            if signup_button:
                result = auth.register(full_name, new_email, new_password, confirm_password)
                if result.ok and result.needs_confirmation:
                    # Supabase email confirmation: not signed in until the emailed code is entered
                    st.session_state[_PENDING_KEY] = new_email.strip().lower()
                    st.rerun()
                elif result.ok:
                    if result.tokens:
                        store_auth_tokens(*result.tokens)
                        queue_cookie_write(result.tokens[1])    # survive a page refresh
                    # new user -> onboarding from step 1 with empty data
                    start_session(result.user, reset_onboarding=True)
                    st.rerun()
                else:
                    st.error(result.error)
