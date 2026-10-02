import streamlit as st

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

    /* Bigger StudentHive title */
    [data-testid="stSidebar"] h1 {
        font-size: 2.6rem;
        font-weight: 800;
        padding-bottom: 0.5rem;
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

    /* Hover for inactive buttons */
    [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
        background-color: #F3F3F3;
        color: #1F1F1F;
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

    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {
        background-color: #F3F3F3;
    }

    /* Active page */
    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"],
    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"]:hover {
        background-color: #FF4B4B;
    }

    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] p,
    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] span {
        color: #FFFFFF;
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


def logout() -> None:
    st.session_state.logged_in = False
    st.session_state.user = None


# ==========================================
# PAGES
# ==========================================

if st.session_state.logged_in:
    pages = {
        "Dashboard": st.Page("views/Dashboard.py", title="Dashboard", default=True),
        "Marketplace": st.Page("views/Marketplace.py", title="Marketplace"),
        "Gigs": st.Page("views/Gigs.py", title="Gigs"),
        "Rentals": st.Page("views/Rentals.py", title="Rentals"),
        "Messages": st.Page("views/Messages.py", title="Messages"),
        "Settings": st.Page("views/Settings.py", title="Settings"),
    }

    # Hide Streamlit's built-in menu, we draw our own below
    pg = st.navigation(list(pages.values()), position="hidden")

    with st.sidebar:
        st.title("StudentHive")
        st.divider()

        for name, page in pages.items():
            st.page_link(page, label=name, use_container_width=True)

        # Keyed container so the CSS above can pin it to the bottom
        with st.container(key="logout_box"):
            st.divider()
            st.button("Logout", use_container_width=True, on_click=logout)

else:
    pg = st.navigation(
        [
            st.Page(
                "views/Login_and_Register.py",
                title="Login",
                url_path="login",
                default=True,
            )
        ],
        position="hidden",
    )

pg.run()