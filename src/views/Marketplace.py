import streamlit as st

from views.components.listing_components import (
    render_listing_detail, render_listing_grid, render_side_panel,
)
from views.CreateListing import render_create_listing, reset_wizard
from views.session import get_marketplace_controller
from views.UserProfileView import render_user_profile
from views.BookingRequest import render_booking_request

def close_profile() -> None:
    st.session_state.viewing_market_profile = None

if st.session_state.get("viewing_market_profile"):
    render_user_profile(st.session_state.viewing_market_profile, on_back=close_profile)
    st.stop()
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
        --orange: #F5A03C;
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

    [data-testid="stMainBlockContainer"] {
        padding-top: 2rem !important;
        padding-bottom: 0 !important;
    }
    [data-testid="stMainBlockContainer"],
    .block-container {
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }

    /* ---------- search box (pill) ---------- */
    [data-testid="stTextInput"] [data-baseweb="input"],
    [data-testid="stTextInput"] [data-baseweb="base-input"] {
        border-radius: 999px;
        background-color: #ffffff;
    }
    [data-testid="stTextInput"] [data-baseweb="input"] { border: 1.5px solid var(--muted); }
    /* newer Streamlit versions: same pill look without data-baseweb */
    [data-testid="stTextInputRootElement"] {
        border: 1.5px solid var(--muted);
        border-radius: 999px;
        background-color: #ffffff;
    }
    [data-testid="stTextInput"] input { color: var(--ink); }

    /* ---------- filter pills (Gig / Rentals) + gig type pills (Service / Project) ---------- */
    .st-key-filter_pills button,
    .st-key-kind_pills button {
        border-radius: 999px;
        border: 1.5px solid var(--ink);
        background: #ffffff;
        min-height: 1.8rem;
        padding: 0 0.9rem;
        box-shadow: none;
    }
    .st-key-filter_pills button p,
    .st-key-kind_pills button p { color: var(--ink); }

    /* hover */
    .st-key-filter_pills button:hover,
    .st-key-kind_pills button:hover {
        border-color: var(--teal);
        background: #ffffff;
    }
    .st-key-filter_pills button:hover p,
    .st-key-kind_pills button:hover p { color: var(--teal); }

    /* clicked / selected: solid teal with white text */
    .st-key-filter_pills [data-testid="stBaseButton-pillsActive"],
    .st-key-filter_pills button[kind="pillsActive"],
    .st-key-filter_pills button[aria-pressed="true"],
    .st-key-filter_pills button[aria-checked="true"],
    .st-key-kind_pills [data-testid="stBaseButton-pillsActive"],
    .st-key-kind_pills button[kind="pillsActive"],
    .st-key-kind_pills button[aria-pressed="true"],
    .st-key-kind_pills button[aria-checked="true"] {
        background: var(--teal) !important;
        border-color: var(--teal) !important;
    }
    .st-key-filter_pills [data-testid="stBaseButton-pillsActive"] p,
    .st-key-filter_pills button[kind="pillsActive"] p,
    .st-key-filter_pills button[aria-pressed="true"] p,
    .st-key-filter_pills button[aria-checked="true"] p,
    .st-key-kind_pills [data-testid="stBaseButton-pillsActive"] p,
    .st-key-kind_pills button[kind="pillsActive"] p,
    .st-key-kind_pills button[aria-pressed="true"] p,
    .st-key-kind_pills button[aria-checked="true"] p {
        color: #ffffff !important;
    }
    .st-key-filter_pills [data-testid="stBaseButton-pillsActive"]:hover,
    .st-key-filter_pills button[kind="pillsActive"]:hover,
    .st-key-kind_pills [data-testid="stBaseButton-pillsActive"]:hover,
    .st-key-kind_pills button[kind="pillsActive"]:hover {
        background: var(--teal-hover) !important;
        border-color: var(--teal-hover) !important;
    }

    /* focus ring after clicking (replaces the default red one) */
    .st-key-filter_pills button:focus,
    .st-key-filter_pills button:focus-visible,
    .st-key-kind_pills button:focus,
    .st-key-kind_pills button:focus-visible {
        outline: none;
        box-shadow: 0 0 0 0.15rem rgba(15, 107, 98, 0.25) !important;
    }

    /* ---------- "Add a Listing" button ---------- */
    .st-key-add_listing_btn button {
        background: var(--teal);
        border: none;
        border-radius: 999px;
        min-height: 1.9rem;
        padding: 0 1rem;
        white-space: nowrap;
    }
    .st-key-add_listing_btn button p {
        color: #ffffff;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .st-key-add_listing_btn button:hover,
    .st-key-add_listing_btn button:focus:not(:active) {
        background: var(--teal-hover);
        border: none;
        color: #ffffff;
    }

    /* ---------- listing cards ---------- */
    [class*="st-key-listingcard_"] {
        background: #ffffff;
        border-radius: 18px;
        padding: 0.7rem 0.7rem 1rem 0.7rem !important;   /* extra space at the bottom */
        box-shadow: 0 2px 12px rgba(27, 42, 65, 0.14);
        gap: 0.3rem;
    }

    /* owner + View row: each column is centered on the row's middle line,
       so the View button sits at the vertical middle of the User profile box */
    [class*="st-key-listingcard_"] [data-testid="stHorizontalBlock"] {
        align-items: center !important;
        margin-bottom: 0.2rem;
    }
    [class*="st-key-listingcard_"] [data-testid="stColumn"] {
        align-self: center !important;
        justify-content: center;
    }
    /* strip any extra space around the profile box and the button so each
       one is exactly as tall as its content (extra space would shift the center) */
    [class*="st-key-listingcard_"] [data-testid="stColumn"] [data-testid="stVerticalBlock"] {
        gap: 0;
    }
    [class*="st-key-listingcard_"] [data-testid="stColumn"] [data-testid="stElementContainer"],
    [class*="st-key-listingcard_"] [data-testid="stColumn"] [data-testid="stMarkdown"],
    [class*="st-key-listingcard_"] [data-testid="stColumn"] [data-testid="stMarkdownContainer"] {
        margin: 0 !important;
        padding: 0 !important;
        min-height: 0;
    }
    [class*="st-key-listingcard_"] [data-testid="stColumn"] [data-testid="stMarkdownContainer"] p {
        margin: 0 !important;
    }
    [class*="st-key-listingcard_"] .stButton { margin: 0; }

    .sh-image {
        position: relative;
        border-radius: 14px;
        overflow: hidden;
        background:
            radial-gradient(ellipse 55% 38% at 22% 108%, #c5dc7a 0 98%, transparent 100%),
            radial-gradient(ellipse 75% 45% at 72% 112%, #8aa300 0 98%, transparent 100%),
            linear-gradient(#bee3fa, #e8f5fd);
    }
    
    .sh-badge-row {
        position: absolute;
        top: 10px;
        left: 10px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .sh-badge {
        background: var(--teal);          /* Gig */
        color: #ffffff;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 2px 14px;
        border-radius: 999px;
    }
    .sh-badge-rental { background: var(--orange); }   /* Rental */
    .sh-badge-kind { background: #b7cee0; color: var(--ink); }   /* Service / Project */

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
        margin-top: 1.5rem;
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
    .sh-divider { border: none; border-top: 1px solid var(--line); margin: 0.2rem 0 0.6rem; }

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
        padding: 0rem 0.5rem;
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

    /* ================= LISTING DETAIL PAGE ================= */

    /* Back button (small outlined pill) */
    .st-key-back_btn button {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 999px;
        min-height: 1.5rem;
        padding: 0 0.7rem;
        box-shadow: none;
    }
    .st-key-back_btn button p {
        color: var(--ink);
        font-size: 1rem;
        font-weight: 500;
    }
    .st-key-back_btn button:hover { border-color: var(--teal); }
    .st-key-back_btn button:hover p { color: var(--teal); }

    /* Gallery: one big picture + two stacked thumbnails */
    .sh-gallery {
        display: grid;
        grid-template-columns: 3.1fr 1fr;
        grid-template-rows: 1fr 1fr;
        gap: 8px;
        height: 450px;
        margin-bottom: 1rem;
    }
    .sh-gallery .sh-image { height: 100%; border-radius: 16px; }
    .sh-gallery .sh-image:first-child { grid-row: 1 / 3; }

    /* Title, meta, About */
    .sh-detail-title {
        font-family: 'Montserrat', sans-serif;
        font-weight: 800;
        font-size: 2.5rem;
        line-height: 1.2;
        color: var(--ink);
    }
    .sh-detail-meta {
        font-family: 'Inter', sans-serif;
        font-size: 0.75rem;
        color: var(--muted);
        margin-top: 0.2rem;
    }
    .sh-detail-divider { border: none; border-top: 1px solid var(--line); margin: 0.8rem 0 1rem; }
    .sh-about-title {
        font-family: 'Montserrat', sans-serif;
        font-weight: 700;
        font-size: 1.5rem;
        color: var(--ink);
        margin-bottom: 0.5rem;
    }
    .sh-about-text {
        font-family: 'Inter', sans-serif;
        font-size: 0.90rem;
        line-height: 1.5;
        color: var(--ink);
        margin-bottom: 1rem;
    }

    /* Side panel box */
    [class*="st-key-detail_panel_"] {
        border: 3px solid var(--line);
        border-radius: 14px;
        padding: 1.2rem 1rem 1rem 1rem !important;
        gap: 0.5rem;
    }
    .sh-panel-price { padding: 0 0.6rem 0.4rem; }
    .sh-panel-price .amt {
        font-family: 'Montserrat', sans-serif;
        font-weight: 800;
        font-size: 1.7rem;
        color: var(--ink);
    }
    .sh-panel-price .per { font-size: 0.7rem; color: var(--teal-soft); margin-left: 0.3rem; }

    .sh-panel-user {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        background: #f0f0f0;
        border: 2px solid var(--line);
        border-radius: 12px;
        padding: 0.7rem 1rem;
        margin-bottom: 3rem;
    }
    .sh-avatar-lg { width: 46px; height: 46px; border-width: 3px; font-size: 1.1rem; }
    .sh-panel-user-name { font-weight: 700; font-size: 0.95rem; color: var(--ink); line-height: 1.2; }
    .sh-panel-user-sub { font-size: 0.65rem; color: var(--muted); }

    /* Message Owner (teal) / Request Booking (yellow-orange) */
    [class*="st-key-message_owner_"] button,
    [class*="st-key-request_booking_"] button {
        border: none;
        border-radius: 8px;
        min-height: 2.2rem;
    }
    [class*="st-key-message_owner_"] button { background: #0b9488; }
    [class*="st-key-message_owner_"] button p { color: #ffffff; font-weight: 700; font-size: 0.85rem; }
    [class*="st-key-message_owner_"] button:hover { background: var(--teal-hover); border: none; }

    [class*="st-key-request_booking_"] button { background: #ffc65c; }
    [class*="st-key-request_booking_"] button p { color: #1b1b1b; font-weight: 700; font-size: 0.85rem; }
    [class*="st-key-request_booking_"] button:hover { background: #f5b23c; border: none; }
    
    /* ---------- Gallery tiles (the button IS the tile) ---------- */
    .st-key-gal_css { display: none; }

    [class*="st-key-gal_big_"], [class*="st-key-gal_thumb_"],
    [class*="st-key-gal_big_"] [data-testid="stButton"], [class*="st-key-gal_thumb_"] [data-testid="stButton"] {
        width: 100% !important;
    }

    /* heights: wrapper + button, so nothing collapses */
    [class*="st-key-gal_big_"], [class*="st-key-gal_big_"] [data-testid="stButton"], [class*="st-key-gal_big_"] button {
        height: 368px !important; min-height: 368px !important;
    }
    [class*="st-key-gal_thumb_"], [class*="st-key-gal_thumb_"] [data-testid="stButton"], [class*="st-key-gal_thumb_"] button {
        height: 176px !important; min-height: 176px !important;
    }

    [class*="st-key-gal_big_"] button, [class*="st-key-gal_thumb_"] button {
        width: 100% !important; padding: 0 !important; border: none !important; border-radius: 14px !important;
        background-color: #cfd8dc !important; background-size: cover !important; background-position: center !important;
        background-repeat: no-repeat !important; cursor: zoom-in;
    }
    [class*="st-key-gal_big_"] button p, [class*="st-key-gal_thumb_"] button p {
        color: #fff !important; font: 600 2rem 'Montserrat', sans-serif !important; margin: 0 !important;
    }
    [class*="st-key-gal_big_"] button:hover, [class*="st-key-gal_thumb_"] button:hover { filter: brightness(.9); }
    [class*="st-key-gal_big_"] button:focus, [class*="st-key-gal_thumb_"] button:focus { outline: none !important; box-shadow: none !important; }
    [class*="st-key-galph_"] [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }

    /* ---------- Lightbox ---------- */
    .sh-lb-img { display: block; width: 100%; max-height: 70vh; object-fit: contain; border-radius: 12px; background: #111; }
    .sh-lb-count { text-align: center; color: var(--muted); margin-top: .5rem; font-size: .9rem; }
    .st-key-lb_prev button, .st-key-lb_next button { border-radius: 50%; width: 44px; height: 44px; padding: 0; background: var(--teal); color: #fff; border: none; }
    .st-key-lb_prev button:hover, .st-key-lb_next button:hover { background: var(--teal-hover); }

    [class*="st-key-profilerow_"] {
        position: relative;
        cursor: pointer;
    }
    [class*="st-key-profilerow_"]:hover .sh-panel-user { background: #e4e7ea; }

    [class*="st-key-profilebtn_"] {
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        width: 100% !important;
        height: 100% !important;
        margin: 0;
        z-index: 5;
    }
    [class*="st-key-profilebtn_"] > div,
    [class*="st-key-profilebtn_"] .stButton {
        width: 100% !important;
        height: 100% !important;
    }
    [class*="st-key-profilebtn_"] button {
        width: 100%;
        height: 100%;
        min-height: 100%;
        padding: 0;
        border: none;
        border-radius: 0.75rem;
        background: transparent;
        box-shadow: none;
        cursor: pointer;
    }
    [class*="st-key-profilebtn_"] button:hover,
    [class*="st-key-profilebtn_"] button:focus:not(:active),
    [class*="st-key-profilebtn_"] button:active {
        background: transparent;
        border: none;
        box-shadow: none;
    }
    [data-testid="stMain"] [class*="st-key-profilebtn_"] button [data-testid="stMarkdownContainer"] p {
        opacity: 0;
    }

    [class*="st-key-profilerow_"],
    [class*="st-key-profilerow_"] > div:not([class*="st-key-profilebtn_"]) {
        flex-shrink: 0 !important;
        height: auto !important;
        min-height: fit-content !important;
    }

    .sh-panel-user { margin-bottom: 0; }

    [class*="st-key-profilerow_"] {
        gap: 0;
        margin-bottom: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# PAGE LOGIC
# ==========================================

market = get_marketplace_controller()


def open_listing(listing_id: int) -> None:
    st.session_state.selected_listing_id = listing_id


def close_listing() -> None:
    st.session_state.selected_listing_id = None

def open_create() -> None:
    """'Add a Listing' clicked: start a fresh wizard and show the Create page."""
    reset_wizard()
    st.session_state.creating_listing = True

selected_id = st.session_state.get("selected_listing_id")
booking_id = st.session_state.get("booking_listing_id")

if st.session_state.get("creating_listing"):
    # ---------- create a listing (4-step wizard) ----------
    render_create_listing(market)

elif booking_id is not None:
    # ---------- booking / project request ----------
    render_booking_request(market, booking_id)

elif selected_id is None:
    # ---------- header: title left, search + filters right ----------
    left, right = st.columns([3, 2], vertical_alignment="top")
    with left:
        st.title("Marketplace")
        st.caption("Browse verified Gigs and Rentals across your campus")
        st.space("small")
    with right:
        query = st.text_input("Search", placeholder="\U0001F50D  Search listings",
                              label_visibility="collapsed", key="market_search")
        add_col, pills_col, kind_col = st.columns([1.2, 1.5, 1.6], vertical_alignment="center")
        with add_col:
            st.button("Add a Listing", icon=":material/add:", key="add_listing_btn",
                      on_click=open_create)
        with pills_col:
            with st.container(key="filter_pills"):
                # single select: one pill at a time, none selected = show everything
                chosen = st.pills("Filter", ["Gig", "Rentals"], selection_mode="single",
                                  label_visibility="collapsed", key="market_filter")

        # Service / Project pills: only shown while "Gig" is selected
        kind_choice = None
        if chosen == "Gig":
            with kind_col:
                with st.container(key="kind_pills"):
                    kind_choice = st.pills("Gig type", ["Service", "Project"],
                                           selection_mode="single",
                                           label_visibility="collapsed", key="market_kind")

    # the pill says "Rentals", the data says "Rental"
    if chosen == "Gig":
        categories = ["Gig"]
    elif chosen == "Rentals":
        categories = ["Rental"]
    else:
        categories = []

    # Service / Project narrows the Gigs; nothing selected = all gigs
    results = market.search(query, categories, deliverable_kind=kind_choice)

    # ---------- grid ----------
    render_listing_grid(results, open_listing, key_prefix="market")

else:
    # ---------- detail view ----------
    entry = market.get_entry(selected_id)
    if entry is None:                      # deleted or closed in the meantime
        close_listing()
        st.rerun()

    back_col, crumb_col = st.columns([1.4, 6], vertical_alignment="center")
    with back_col:
        st.button("Back to Marketplace", on_click=close_listing, key="back_btn")

    main_col, side_col = st.columns([2.7, 1], gap="large")
    with main_col:
        render_listing_detail(entry)
    with side_col:
        render_side_panel(entry)