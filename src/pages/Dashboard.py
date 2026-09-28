from html import escape

import streamlit as st

# ---------- Page-specific styles ----------
st.markdown(
    """
    <style>
    html, body,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
        overflow: hidden !important;
    }

    [data-testid="stMainBlockContainer"] {
        padding-top: 2rem !important;
        padding-bottom: 0 !important;
    }iv
    [data-testid="stMainBlockContainer"],
    .block-container {
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }
    /* Dark text everywhere in the main area */
    [data-testid="stMain"],
    [data-testid="stMain"] label,
    [data-testid="stMain"] [data-testid="stCaptionContainer"],
    [data-testid="stMain"] [data-testid="stMarkdownContainer"],
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] :is(h1, h2, h3, h4, h5, h6, p, span, li, strong, em) {
        color: #1F1F1F !important;
    }

    /* Keep the Gig / Rental badge text white */
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] .badge.badge {
        color: #FFFFFF !important;
    }

    /* White dashboard background (including Streamlit's top bar) */
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stHeader"] {
        background-color: #FFFFFF !important;
    }

    /* Dark text so it shows on white (:where keeps the badge text white) */
    [data-testid="stMain"] :where(h1, h2, h3, h4, p, label) {
        color: #1F1F1F;
    }
    [data-testid="stToolbar"] {
        color: #1F1F1F;
    }

    /* Top header: #e7edf1, no border */
    .st-key-header_box,
    [data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-header_box) {
        background-color: #e7edf1;
        border: none;
        border-radius: 1rem;
    }

    /* Softer borders on the other boxes so they suit a white page */
    [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #E2E6EA;
    }

    .avatar-placeholder {
        width: 90px;
        height: 90px;
        margin: 0 auto;          /* centers the circle in its column */
        border-radius: 50%;
        background: #F5B301;
        border: 3px solid #E0A100;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 40px;
    }

    .listing-grid {
        display: grid;
        grid-template-columns: 1fr;   /* one card per row */
        gap: 1rem;
    }

    .listing-card {
        display: flex;
        height: 134px;
        background: #FFFFFF;
        border-radius: 1rem;
        overflow: hidden;
        box-shadow: 0 0 12px rgba(0, 0, 0, 0.25);   /* slight black glow */
    }

    .listing-card img {
        width: 38%;
        height: 100%;
        object-fit: cover; 
        display: block;
        flex-shrink: 0;
    }

    .listing-info {
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 0.6rem;
        padding: 0 1.25rem;
        min-width: 0;
    }

    .listing-name {
        font-weight: 700;
        font-size: 1.05rem;
        color: #1F1F1F;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .listing-meta {
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }

    .badge {
        padding: 0.2rem 0.9rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 700;
        color: #FFFFFF;
    }
    .badge-gig    { background: #0F9D8A; }
    .badge-rental { background: #F5A03C; }

    .listing-price {
        font-weight: 700;
        font-size: 0.9rem;
        color: #1F1F1F;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Helpers ----------
def listing_card(item: dict) -> str:
    """Build one listing card as a single-line HTML string.

    No indentation or blank lines on purpose: Markdown treats lines
    indented 4+ spaces as a code block and would print the raw HTML.
    """
    badge_class = "badge-gig" if item["label"] == "Gig" else "badge-rental"
    return (
        '<div class="listing-card">'
        f'<img src="{escape(item["image"])}">'
        '<div class="listing-info">'
        f'<div class="listing-name">{escape(item["name"])}</div>'
        '<div class="listing-meta">'
        f'<span class="badge {badge_class}">{escape(item["label"])}</span>'
        f'<span class="listing-price">{escape(item["price"])}</span>'
        '</div>'
        '</div>'
        '</div>'
    )


user = st.session_state.get("user") or {}
name = user.get("name", "User")

# ---------- Header ----------
with st.container(border=True, key="header_box"):
    col_img, col_text = st.columns([1, 6], vertical_alignment="center")

    with col_img:
        st.markdown('<div class="avatar-placeholder">👤</div>', unsafe_allow_html=True)

    with col_text:
        st.header(f"Welcome, {name}!")
        st.subheader("Here’s what’s happening in your hive today.")

left_col, right_col = st.columns([2, 1])

# ---------- Left: listings ----------
with left_col:
    st.subheader("My Listings")

    listings = [
        {"image": "https://placehold.co/200", "name": "Math Tutoring", "label": "Gig", "price": "₱150/hr"},
        {"image": "https://placehold.co/200", "name": "Studio Apartment", "label": "Rental", "price": "₱8,000/mo"},
        {"image": "https://placehold.co/200", "name": "Dog Walking", "label": "Gig", "price": "₱100/hr"},
        {"image": "https://placehold.co/200", "name": "Cleaning", "label": "Gig", "price": "₱100/hr"},
    ]

    cards_html = "".join(listing_card(item) for item in listings)

    with st.container(height=665, border=True):
        st.markdown(
            f'<div class="listing-grid">{cards_html}</div>',
            unsafe_allow_html=True,
        )

# ---------- Right: gigs / rentals ----------
with right_col:
    st.subheader("")

    with st.container(border=True):
        st.subheader("Gigs")
        st.write("Content goes here.")
        st.write("Content goes here.")
        st.write("Content goes here.")

    with st.container(border=True):
        st.subheader("Rentals")
        st.write("Content goes here.")
        st.write("Content goes here.")