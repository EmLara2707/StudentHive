import streamlit as st
from pages import Dashboard as dashboard_page

st.set_page_config(page_title="StudentHive", layout="wide")

# ==========================================
# SESSION STATE
# ==========================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = True  # TEMP OVERRIDE: was False

if "user" not in st.session_state:
    st.session_state.user = {"name": "Test User"}  # TEMP: fake user for dev

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"


# ==========================================
# LOGIN / REGISTRATION (gate)
# ==========================================
# TEMP: bypassed while loginAndRegister.py doesn't exist yet.
# Restore this block once the login page is built:
#
# if not st.session_state.logged_in:
#     loginAndRegister.render()
#
# else:

if True:  # TEMP: replace with `else:` above once login gate is restored

    PAGES = ["Dashboard", "Marketplace", "Gigs", "Rentals", "Messages", "Settings"]

    with st.sidebar:

        st.title("StudentHive")

        st.divider()

        for page in PAGES:
            if st.button(page, use_container_width=True,
                          type="primary" if st.session_state.page == page else "secondary",
                          key=f"nav_{page}"):
                st.session_state.page = page

        st.divider()

        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.page = "Dashboard"
            st.rerun()

    def marketplace():
        st.header("🏪 Marketplace")
        st.write("Browse and purchase items here.")

    def messages():
        st.header("💬 Messages")
        st.write("View and manage your messages here.")

    def gigs():
        st.header("ℹ️ Gigs")
        st.write("Info about gigs.")

    def rentals():
        st.header("🏠 Rentals")
        st.write("View and manage rental properties here.")

    def settings():
        st.header("⚙️ Settings")
        st.write("Configure app settings here.")

    page_funcs = {
        "Dashboard": dashboard_page.render,
        "Marketplace": marketplace,
        "Gigs": gigs,
        "Rentals": rentals,
        "Messages": messages,
        "Settings": settings,
    }

    page_funcs[st.session_state.page]()