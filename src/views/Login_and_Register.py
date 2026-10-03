import os
import streamlit as st

# NOTE: do NOT call st.set_page_config here. app.py already does it.

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Montserrat:wght@700&display=swap');

    :root {
        --teal: #0f6b62;
        --teal-hover: #0b5750;
        --teal-soft: #3f8f86;
        --ink: #3a3d3f;
        --muted: #5b6770;
        --line: #dcdfe2;
    }

    html, body, .stApp, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background: #ffffff;
    }

    /* ---------- page frame ---------- */
    /* no page scroll (also removes the scrollbar on the right) */
    html, body,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
        overflow: hidden !important;
    }

    /* remove header, toolbar, colored top bar, and the (empty) sidebar */
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"] {
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

    /* ---------- left image ---------- */
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
        border-radius: 0 !important;
        display: block;
    }

    /* ---------- right panel ---------- */
    .st-key-form_panel {
        padding: 0 4rem;
        width: 100%;
        max-width: 640px;
        margin: 0 auto;      /* centers the form inside the right column */
    }

    .sh-title {
        font-family: 'Montserrat', sans-serif;
        font-weight: 700;
        font-size: 2.2rem;
        line-height: 1.2;
        color: var(--ink);
        margin: 0 0 1.5rem 0;
    }
    .sh-sub {
        font-size: 1.3rem;
        line-height: 1.5;
        color: var(--muted);
        margin-bottom: 1.8rem;
    }

    /* ---------- tabs ---------- */
    [data-testid="stTabs"] [role="tablist"],
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 3px solid var(--line);
    }

    [data-testid="stTab"],
    .stTabs [data-baseweb="tab"] {
        flex: 1;
        justify-content: center;
        height: 48px;
        background: transparent;
    }

    /* unselected tab text: same ink color as the rest of the page text */
    [data-testid="stTab"] [data-testid="stMarkdownContainer"] p,
    .stTabs [data-baseweb="tab"] p {
        font-weight: 600;
        font-size: 1.1rem;
        color: var(--ink) !important;
    }

    /* hover */
    [data-testid="stTab"]:hover [data-testid="stMarkdownContainer"] p {
        color: var(--teal) !important;
    }

    /* selected tab text */
    [data-testid="stTab"][aria-selected="true"] [data-testid="stMarkdownContainer"] p,
    .stTabs [aria-selected="true"] p {
        color: var(--teal) !important;
    }

    /* underline under the selected tab */
    [data-testid="stTab"] .react-aria-SelectionIndicator,
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: var(--teal) !important;
        height: 3px;
    }
    .stTabs [data-baseweb="tab-border"] {
        display: none;
    }

    /* ---------- field labels ---------- */
    [data-testid="stWidgetLabel"] p {
        font-size: 1.15rem !important;
        font-weight: 500;
        color: var(--ink);
        margin-bottom: 0.25rem;
    }

    /* ---------- button ---------- */
    .stButton {
        display: flex;
        justify-content: center;
        margin-top: 1.5rem;
    }
    .stButton > button {
        background: var(--teal);
        border: none;
        border-radius: 14px;
        padding: 0.7rem 2.6rem;
        min-height: 54px;
    }
    .stButton > button p {
        color: #ffffff;
        font-weight: 600;
        font-size: 1.1rem;
    }
    .stButton > button:hover,
    .stButton > button:focus:not(:active) {
        background: var(--teal-hover);
        border: none;
        color: #ffffff;
    }

    /* ---------- legal text ---------- */
    .sh-legal {
        text-align: center;
        font-size: 0.9rem;
        line-height: 1.6;
        color: var(--muted);
        margin-top: 1.2rem;
    }
    .sh-legal a { color: var(--teal-soft); text-decoration: none; }
    </style>
    """,
    unsafe_allow_html=True,
)


def find_image() -> str | None:
    """Look for the image next to this file, then one folder up (project root)."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "images", "LoginAndRegister.png"),
        os.path.join(base_dir, "..", "images", "LoginAndRegister.png"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


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
                if not school_email or not password:
                    st.error("Please fill in all fields.")
                else:
                    # TODO: replace with a real credential check
                    st.session_state.logged_in = True
                    st.session_state.user = {
                        "name": school_email.split("@")[0],
                        "email": school_email,
                    }
                    st.rerun()

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
                if not full_name or not new_email or not new_password or not confirm_password:
                    st.error("Please fill in all fields.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    # TODO: save the account to your database
                    st.success("Account created! Check your school email to verify it.")