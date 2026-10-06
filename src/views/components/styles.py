"""View-layer helper that injects CSS files from views/styles/."""
from pathlib import Path

import streamlit as st

_STYLES_DIR = Path(__file__).resolve().parent.parent / "styles"


def load_css(*names: str) -> None:
    """Inject base.css followed by each named stylesheet (e.g. load_css("login"))."""
    ordered = ["base"] + [n for n in names if n != "base"]
    css = "\n".join(
        (_STYLES_DIR / f"{n}.css").read_text(encoding="utf-8") for n in ordered
    )
    st.markdown(f"<style>\n{css}\n</style>", unsafe_allow_html=True)
