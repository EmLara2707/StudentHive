import streamlit as st

st.set_page_config(page_title="StudentHive", layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "Home"

PAGES = ["Dashboard", "Marketplace", "Gigs", "Rentals", "Messages", "Settings"]

with st.sidebar:
    st.title("StudentHive")
    for page in PAGES:
        if st.button(page, use_container_width=True,
                      type="primary" if st.session_state.page == page else "secondary"):
            st.session_state.page = page

def dashboard():
    st.header("📊 Dashboard")
    st.write("Charts and metrics go here.")

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
    "Dashboard": dashboard,
    "Marketplace": marketplace,
    "Gigs": gigs,
    "Rentals": rentals,
    "Messages": messages,
    "Settings": settings,
}

page_funcs[st.session_state.page]()