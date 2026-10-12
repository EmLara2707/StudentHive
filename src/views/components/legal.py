"""Terms of Service and Privacy Policy dialogs, opened from the sign-up page.
The text lives in views/legal/*.md so it can be edited without touching code."""
from pathlib import Path

import streamlit as st

# Put the team's real contact email here (one place; both documents use it).
CONTACT_EMAIL = "stdnt.hive@gmail.com"

_LEGAL_DIR = Path(__file__).resolve().parent.parent / "legal"


def _text(name: str) -> str:
    try:
        return (_LEGAL_DIR / name).read_text(encoding="utf-8").replace("{contact}", CONTACT_EMAIL)
    except OSError:
        return "This document couldn't be loaded. Please try again later."


def _show(body_file: str, close_key: str) -> None:
    with st.container(height=420, border=False):
        st.markdown(_text(body_file))
    if st.button("Close", key=close_key):
        st.rerun()


@st.dialog("Terms of Service", width="large")
def terms_dialog() -> None:
    _show("terms_of_service.md", "terms_close")


@st.dialog("Privacy Policy", width="large")
def privacy_dialog() -> None:
    _show("privacy_policy.md", "privacy_close")
