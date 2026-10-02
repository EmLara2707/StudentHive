import sys
from pathlib import Path

import streamlit as st

# make `models.py` (in src/) importable from pages/
sys.path.append(str(Path(__file__).resolve().parent.parent))

from views.Listing import get_marketplace, render_listing_grid

# ==========================================
# STYLES (Marketplace page only)
# ==========================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Montserrat:wght@700;800&display=swap');

    :root {
        --teal: #0f6b62;
        --teal-hover: #0b5750;
        --teal-soft: #3f8f86;
        --mint: #4ccfc0;
        --ink: #3a3d3f;
        --muted: #5b6770;
        --line: #dcdfe2;
    }

    /* ---------- main area ---------- */
    [data-testid="stMain"] {
        background: #ffffff;
        color: var(--ink);
    }
    [data-testid="stMain"] p,
    [data-testid="stMain"] button,
    [data-testid="stMain"] input {
        font-family: 'Inter', sans-serif;
    }
    [data-testid="stMain"] h1 {
        font-family: 'Montserrat', sans-serif;
        font-weight: 800;
        color: var(--ink);
        padding-bottom: 0;
    }
    [data-testid="stMain"] h2,
    [data-testid="stMain"] h3 { color: var(--ink); }

    /* ---------- search box (pill) ---------- */
    [data-testid="stTextInput"] [data-baseweb="input"],
    [data-testid="stTextInput"] [data-baseweb="base-input"] {
        border-radius: 999px;
        background-color: #ffffff;
    }
    [data-testid="stTextInput"] [data-baseweb="input"] { border: 1.5px solid var(--muted); }
    [data-testid="stTextInput"] input { color: var(--ink); }

    /* ---------- filter pills ---------- */
    .st-key-filter_pills [data-testid="stPills"],
    .st-key-filter_pills > div { justify-content: flex-end; }

    .st-key-filter_pills button {
        border-radius: 999px;
        border: 1.5px solid var(--ink);
        background: #ffffff;
        color: var(--ink);
        min-height: 1.8rem;
        padding: 0 0.9rem;
    }
    .st-key-filter_pills button[kind="pillsActive"],
    .st-key-filter_pills button[aria-checked="true"] {
        background: var(--teal);
        border-color: var(--teal);
    }
    .st-key-filter_pills button[kind="pillsActive"] p,
    .st-key-filter_pills button[aria-checked="true"] p { color: #ffffff; }

    /* ---------- listing cards ---------- */
    [class*="st-key-listingcard_"] {
        background: #ffffff;
        border-radius: 18px;
        padding: 0.7rem;
        box-shadow: 0 2px 12px rgba(27, 42, 65, 0.14);
        gap: 0.4rem;
    }

    .sh-image {
        position: relative;
        border-radius: 14px;
        overflow: hidden;
        background:
            radial-gradient(ellipse 55% 38% at 22% 108%, #c5dc7a 0 98%, transparent 100%),
            radial-gradient(ellipse 75% 45% at 72% 112%, #8aa300 0 98%, transparent 100%),
            linear-gradient(#bee3fa, #e8f5fd);
    }
    .sh-badge {
        position: absolute;
        top: 10px;
        left: 10px;
        background: var(--teal);
        color: #ffffff;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 2px 14px;
        border-radius: 999px;
    }
    .sh-cloud {
        position: absolute;
        top: 16px;
        right: 22%;
        width: 44px;
        height: 16px;
        background: #ffffff;
        border-radius: 999px;
        box-shadow: 14px -8px 0 2px #ffffff;
    }

    .sh-title-row {
        display: flex;
        justify-content: space-between;
        gap: 0.5rem;
        margin-top: 0.4rem;
    }
    .sh-card-title {
        font-family: 'Montserrat', sans-serif;
        font-weight: 700;
        font-size: 1rem;
        line-height: 1.3;
        color: var(--ink);
        min-height: 2.6em;      /* keeps cards aligned for 1 or 2 line titles */
    }
    .sh-price {
        font-weight: 600;
        font-size: 0.85rem;
        color: var(--ink);
        white-space: nowrap;
    }
    .sh-divider { border: none; border-top: 1px solid var(--line); margin: 0.4rem 0 0.2rem; }

    .sh-owner { display: flex; align-items: center; gap: 0.6rem; }
    .sh-avatar {
        width: 38px;
        height: 38px;
        border: 2px solid var(--mint);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--teal);
        font-weight: 600;
        flex-shrink: 0;
    }
    .sh-owner-name { font-weight: 600; font-size: 0.8rem; line-height: 1.2; color: var(--ink); }
    .sh-owner-course { font-size: 0.7rem; color: var(--muted); }

    /* teal "View" pill inside cards */
    [class*="st-key-listingcard_"] button {
        background: var(--teal);
        border: none;
        border-radius: 999px;
        min-height: 1.9rem;
        padding: 0 0.5rem;
    }
    [class*="st-key-listingcard_"] button p {
        color: #ffffff;
        font-weight: 600;
        font-size: 0.8rem;
    }
    [class*="st-key-listingcard_"] button:hover,
    [class*="st-key-listingcard_"] button:focus:not(:active) {
        background: var(--teal-hover);
        border: none;
        color: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# PAGE LOGIC
# ==========================================

market = get_marketplace()


def open_listing(listing_id: int) -> None:
    st.session_state.selected_listing_id = listing_id


def close_listing() -> None:
    st.session_state.selected_listing_id = None


selected_id = st.session_state.get("selected_listing_id")

if selected_id is None:
    # ---------- header: title left, search + filters right ----------
    left, right = st.columns([3, 2], vertical_alignment="top")
    with left:
        st.title("Marketplace")
        st.caption("Browse verified Gigs and Rentals across your campus")
    with right:
        query = st.text_input("Search", placeholder="\U0001F50D  Search listings",
                              label_visibility="collapsed", key="market_search")
        with st.container(key="filter_pills"):
            chosen = st.pills("Filter", ["Gig", "Rentals"], selection_mode="multi",
                              label_visibility="collapsed", key="market_filter")

    # the pill says "Rentals", the data says "Rental"
    categories = ["Rental" if c == "Rentals" else c for c in (chosen or [])]

    # ---------- grid ----------
    render_listing_grid(market.search(query, categories), open_listing, key_prefix="market")

else:
    # ---------- detail view ----------
    listing = market.get_listing(selected_id)
    st.button("\u2190 Back to Marketplace", on_click=close_listing, key="back_btn")

    main_col, side_col = st.columns([2, 1])
    with main_col:
        listing.render_detail()
    with side_col:
        listing.render_side_panel()