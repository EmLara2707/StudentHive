import streamlit as st
from views.session import end_session
st.set_page_config(page_title="StudentHive", layout="wide")


# ==========================================
# GLOBAL STYLES (spacing + sidebar)
# ==========================================

st.markdown(
    """
    <style>
    /* Sidebar background */
    [data-testid="stSidebar"] {
        background-color: #E7EDF1;
    }

    /* Text colors so they show on the light sidebar */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {
        color: #1F1F1F;
    }

    /* Bigger StudentHive title, in the brand green */
    [data-testid="stSidebar"] h1 {
        font-size: 2.6rem;
        font-weight: 800;
        padding-bottom: 0.5rem;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h1 span,
    [data-testid="stSidebar"] h1 a {
        color: #0c9488 !important;
    }

    /* Dividers */
    [data-testid="stSidebar"] hr {
        border-color: #E5E5E5;
        margin: 0.5rem 0;
    }

    /* Tighter spacing between sidebar elements */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.50rem;
    }

    /* Buttons: no border, left-aligned, compact */
    [data-testid="stSidebar"] .stButton > button {
        border: none;
        box-shadow: none;
        background-color: transparent;
        color: #1F1F1F;
        justify-content: flex-start;
        text-align: left;
        min-height: 2.2rem;
        padding-top: 0.50rem;
        padding-bottom: 0.50rem;
    }

    [data-testid="stSidebar"] .stButton > button > div {
        justify-content: flex-start;
        text-align: left;
        width: 100%;
    }

    /* Hover / press for buttons (Logout) */
    [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
        background-color: #D3E3EE !important;
        color: #1F1F1F;
    }
    [data-testid="stSidebar"] .stButton > button[kind="secondary"]:active,
    [data-testid="stSidebar"] .stButton > button[kind="secondary"]:focus:not(:active) {
        background-color: #B0CDE1 !important;
        color: #1F1F1F;
        box-shadow: none;
        outline: none;
    }

    /* ---------- Nav links (st.page_link) ---------- */
    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {
        justify-content: flex-start;
        text-align: left;
        min-height: 2.6rem;
        padding: 0.25rem 0.75rem;
        border: none;
        border-radius: 0.5rem;
        background-color: transparent;
        text-decoration: none;
    }

    /* hover: soft tint, lighter than the selected color */
    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {
        background-color: #D3E3EE !important;
    }

    /* pressing: same as the selected color */
    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:active,
    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:focus:not(:active) {
        background-color: #B0CDE1 !important;
        outline: none;
        box-shadow: none;
    }

    /* Active page: light blue with dark text, like the design */
    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"],
    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"]:hover {
        background-color: #B0CDE1 !important;
    }

    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] p,
    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] span {
        color: #1F1F1F;
        font-weight: 600;
    }

    /* ---------- Bigger button text ---------- */
    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] p,
    [data-testid="stSidebar"] .stButton > button p {
        font-size: 1.15rem;
        font-weight: 500;
    }

    /* ---------- Logout pinned to the bottom of the sidebar ---------- */
    [data-testid="stSidebarContent"] {
        position: relative;
        height: 100%;
    }

    .st-key-logout_box {
        position: absolute;
        bottom: 1rem;
        left: 1rem;
        right: 1rem;
    }
        /* ---------- Logout confirmation dialog ---------- */
    .st-key-logout_yes button {
        background: #0f6b62 !important;
        border: none !important;
        border-radius: 999px !important;
        min-height: 1.9rem;
        padding: 0 1.3rem !important;
    }
    .st-key-logout_yes button p { color: #ffffff !important; font-weight: 600; font-size: 0.85rem; }
    .st-key-logout_yes button:hover { background: #0b5750 !important; }

    .st-key-logout_no button {
        background: #ffffff !important;
        border: 1.5px solid #0f6b62 !important;
        border-radius: 999px !important;
        min-height: 1.9rem;
        padding: 0 1.3rem !important;
    }
    .st-key-logout_no button p { color: #0f6b62 !important; font-weight: 600; font-size: 0.85rem; }
    .st-key-logout_no button:hover { background: #effaf8 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# SESSION STATE
# ==========================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None

if "onboarding_complete" not in st.session_state:
    st.session_state.onboarding_complete = False

@st.dialog("Log out?")
def confirm_logout_dialog() -> None:
    st.write("You’ll need to sign in again to get back to your account.")
    with st.container(horizontal=True, horizontal_alignment="distribute"):
        if st.button("Cancel", key="logout_no"):
            st.rerun()
        if st.button("Yes, log out", key="logout_yes"):
            end_session()
            st.rerun()

# ==========================================
# PAGES
# ==========================================

if st.session_state.logged_in and not st.session_state.onboarding_complete:
    pg = st.navigation(
        [
            st.Page(
                "views/pages/onboarding.py",
                title="Onboarding",
                url_path="onboarding",
                default=True,
            )
        ],
        position="hidden",
    )

elif st.session_state.logged_in:
    pages = {
        "Profile": st.Page("views/pages/profile.py", title="Profile"),
        "Dashboard": st.Page("views/Dashboard.py", title="Dashboard", default=True),
        "Marketplace": st.Page("views/Marketplace.py", title="Marketplace"),
        "Gigs": st.Page("views/Gigs.py", title="Gigs"),
        "Rentals": st.Page("views/Rentals.py", title="Rentals"),
        "Messages": st.Page("views/Messages.py", title="Messages"),
    }

    # Hide Streamlit's built-in menu, we draw our own below
    pg = st.navigation(list(pages.values()), position="hidden")

    # Keep the current page's link highlighted (each link sits in its own keyed container)
    current = next(n for n, p in pages.items() if p.title == pg.title)
    active = f'.st-key-nav_{current} [data-testid="stPageLink-NavLink"]'
    st.markdown(
        f"""
        <style>
        {active}, {active}:hover {{
            background-color: #B0CDE1 !important;
        }}
        {active} p, {active} span {{
            color: #1F1F1F;
            font-weight: 600;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.title("StudentHive")
        st.divider()

        for name, page in pages.items():
            with st.container(key=f"nav_{name}"):
                st.page_link(page, label=name, use_container_width=True)

        # Keyed container so the CSS above can pin it to the bottom
        with st.container(key="logout_box"):
            st.divider()
            if st.button("Logout", use_container_width=True):
                confirm_logout_dialog()

else:
    pg = st.navigation(
        [
            st.Page(
                "views/pages/login_and_register.py",
                title="Login",
                url_path="login",
                default=True,
            )
        ],
        position="hidden",
    )

pg.run()