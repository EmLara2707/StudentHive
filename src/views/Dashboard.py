import calendar
from collections import defaultdict
from datetime import date, timedelta
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
    }
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

    /* ---------- Calendar dialog ---------- */

    /* The full-screen overlay: blur + dim the dashboard behind it */
    div[data-testid="stDialog"] {
        background: rgba(255, 255, 255, 0.35) !important;
        backdrop-filter: blur(6px);
        -webkit-backdrop-filter: blur(6px);
    }

    /* The actual dialog card: solid white */
    div[data-testid="stDialog"] > div {
        background: #FFFFFF !important;
        border-radius: 1rem;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
    }

    div[data-testid="stDialog"] * {
        color: #1F1F1F !important;
    }

    div[data-testid="stDialog"] .stButton > button {
        background: #F4F6F8 !important;
        border: 1px solid #E2E6EA !important;
        box-shadow: none !important;
        color: #1F1F1F !important;
    }
    div[data-testid="stDialog"] .stButton > button:hover {
        background: #E7EDF1 !important;
    }

    /* Close (×) button */
    div[data-testid="stDialog"] [data-testid="stBaseButton-header-no-border"],
    div[data-testid="stDialog"] button[aria-label="Close"] {
        color: #1F1F1F !important;
    }

    /* ---------- Mini calendar ---------- */
    .st-key-cal_box [data-testid="stVerticalBlock"],
    .st-key-cal_box [data-testid="stHorizontalBlock"] {
        gap: 0.25rem;
    }

    .st-key-cal_box .stButton > button {
        position: relative;          /* lets the event dot sit inside the button */
        min-height: 2.6rem;
        padding: 0;
        border: none;
        border-radius: 0.6rem;
        background: #F4F6F8;
        box-shadow: none;
    }
    .st-key-cal_box .stButton > button:hover {
        background: #E7EDF1;
    }
    .st-key-cal_box .stButton > button p {
        font-size: 0.9rem;
        font-weight: 600;
    }

    .cal-title {
        text-align: center;
        font-weight: 700;
        font-size: 1.05rem;
    }

    .cal-week {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 0.25rem;
        text-align: center;
        font-size: 0.75rem;
        font-weight: 700;
        color: #6B7785;
    }

    .cal-legend {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.4rem;
        font-size: 0.8rem;
        margin-top: 0.4rem;
    }
    .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }
    .dot-gig    { background: #0F9D8A; }
    .dot-rental { background: #F5A03C; margin-left: 0.6rem; }

    .next-title {
        font-weight: 700;
        font-size: 0.9rem;
        margin: 0.6rem 0 0.4rem;
    }

    /* ---------- Event rows (Next up + dialog agenda) ---------- */
    .ev-row {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.45rem 0.6rem;
        margin-bottom: 0.4rem;
        border-radius: 0.75rem;
        background: #F4F6F8;
    }
    .ev-date {
        width: 2.6rem;
        text-align: center;
        flex-shrink: 0;
    }
    .ev-mon {
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        color: #6B7785;
    }
    .ev-day {
        font-size: 1.15rem;
        font-weight: 800;
        line-height: 1.1;
    }
    .ev-info {
        flex: 1;
        min-width: 0;
    }
    .ev-title {
        font-weight: 700;
        font-size: 0.9rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .ev-sub {
        font-size: 0.75rem;
        color: #6B7785;
    }

    /* ---------- Detailed calendar (dialog) ---------- */
    .dlg-title {
        text-align: center;
        font-weight: 800;
        font-size: 1.3rem;
    }
    .dgrid {
        display: grid;
        grid-template-columns: repeat(7, minmax(0, 1fr));
        gap: 0.4rem;
        margin-bottom: 1rem;
    }
    .dhead {
        text-align: center;
        font-size: 0.8rem;
        font-weight: 700;
        color: #6B7785;
    }
    .dcell {
        min-height: 88px;
        padding: 0.4rem;
        border-radius: 0.6rem;
        background: #F4F6F8;
        overflow: hidden;
    }
    .dcell-empty { background: transparent; }
    .dcell-today { box-shadow: inset 0 0 0 2px #0F9D8A; }
    .dcell-sel   { background: #E7EDF1; }
    .dnum {
        font-size: 0.85rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    .chip {
        font-size: 0.7rem;
        font-weight: 600;
        color: #FFFFFF;
        padding: 0.1rem 0.4rem;
        margin-bottom: 0.2rem;
        border-radius: 0.4rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .chip-gig    { background: #0F9D8A; }
    .chip-rental { background: #F5A03C; }
    .chip-more {
        font-size: 0.7rem;
        color: #6B7785;
    }

    /* ---------- Listings ---------- */
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
        box-shadow: 0 2px 12px rgba(27, 42, 65, 0.14);   /* slight black glow */
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


# ==========================================
# SAMPLE EVENTS (replace with database data later)
# Each event needs: date (datetime.date), title, type ("Gig" / "Rental"),
# time, price
# ==========================================

today = date.today()

events = [
    {"date": today + timedelta(days=1),  "title": "Math Tutoring",            "type": "Gig",    "time": "4:00 PM",  "price": "₱150/hr"},
    {"date": today + timedelta(days=3),  "title": "Studio Apartment viewing", "type": "Rental", "time": "10:00 AM", "price": "₱8,000/mo"},
    {"date": today + timedelta(days=3),  "title": "Dog Walking",              "type": "Gig",    "time": "5:30 PM",  "price": "₱100/hr"},
    {"date": today + timedelta(days=6),  "title": "Cleaning",                 "type": "Gig",    "time": "9:00 AM",  "price": "₱100/hr"},
    {"date": today + timedelta(days=9),  "title": "Room move-in",             "type": "Rental", "time": "1:00 PM",  "price": "₱5,500/mo"},
    {"date": today + timedelta(days=15), "title": "Math Tutoring",            "type": "Gig",    "time": "4:00 PM",  "price": "₱150/hr"},
]
events.sort(key=lambda e: e["date"])

events_by_day = defaultdict(list)
for e in events:
    events_by_day[e["date"]].append(e)


# ==========================================
# HELPERS
# ==========================================

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


def event_row(e: dict) -> str:
    badge_class = "badge-gig" if e["type"] == "Gig" else "badge-rental"
    return (
        '<div class="ev-row">'
        '<div class="ev-date">'
        f'<div class="ev-mon">{e["date"]:%b}</div>'
        f'<div class="ev-day">{e["date"].day}</div>'
        '</div>'
        '<div class="ev-info">'
        f'<div class="ev-title">{escape(e["title"])}</div>'
        f'<div class="ev-sub">{escape(e["time"])} · {escape(e["price"])}</div>'
        '</div>'
        f'<span class="badge {badge_class}">{escape(e["type"])}</span>'
        '</div>'
    )


def shift_month(key: str, delta: int) -> None:
    """Callback: move the month stored in session_state[key] by delta months."""
    m = st.session_state[key]
    idx = m.year * 12 + (m.month - 1) + delta
    st.session_state[key] = date(idx // 12, idx % 12 + 1, 1)


def dialog_go_today() -> None:
    st.session_state.dlg_month = date.today().replace(day=1)
    st.session_state.dlg_selected = date.today()


def marker_css(view: date) -> str:
    """Dots under days that have events, plus a highlight for today."""
    rules = []
    base = (
        "content:'';position:absolute;bottom:5px;left:50%;"
        "width:6px;height:6px;border-radius:50%;"
    )
    for d, evs in events_by_day.items():
        if (d.year, d.month) != (view.year, view.month):
            continue
        types = {e["type"] for e in evs}
        sel = f".st-key-cal_box .st-key-day_{d:%Y%m%d} button::after"
        if len(types) > 1:  # gig + rental on the same day: two dots
            rules.append(
                f"{sel}{{{base}background:#0F9D8A;"
                "box-shadow:10px 0 0 #F5A03C;transform:translateX(-8px);}"
            )
        else:
            color = "#0F9D8A" if "Gig" in types else "#F5A03C"
            rules.append(f"{sel}{{{base}background:{color};transform:translateX(-3px);}}")

    if (today.year, today.month) == (view.year, view.month):
        rules.append(
            f".st-key-cal_box .st-key-day_{today:%Y%m%d} button{{background:#CDEEE9;}}"
        )
    return "<style>" + "".join(rules) + "</style>" if rules else ""


# ==========================================
# DETAILED CALENDAR (dialog)
# ==========================================

@st.dialog("Schedule", width="large")
def calendar_dialog() -> None:
    view = st.session_state.dlg_month
    selected = st.session_state.dlg_selected

    prev_col, title_col, next_col, today_col = st.columns([1, 4, 1, 2], vertical_alignment="center")
    prev_col.button("‹", key="dlg_prev", on_click=shift_month, args=("dlg_month", -1), use_container_width=True)
    title_col.markdown(f'<div class="dlg-title">{view:%B %Y}</div>', unsafe_allow_html=True)
    next_col.button("›", key="dlg_next", on_click=shift_month, args=("dlg_month", 1), use_container_width=True)
    today_col.button("Today", key="dlg_today", on_click=dialog_go_today, use_container_width=True)

    # Month grid with event chips
    html = '<div class="dgrid">'
    html += "".join(
        f'<div class="dhead">{n}</div>'
        for n in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    )
    for week in calendar.Calendar(firstweekday=6).monthdayscalendar(view.year, view.month):
        for day in week:
            if day == 0:
                html += '<div class="dcell dcell-empty"></div>'
                continue
            d = date(view.year, view.month, day)
            classes = "dcell"
            if d == today:
                classes += " dcell-today"
            if d == selected:
                classes += " dcell-sel"
            day_events = events_by_day.get(d, [])
            chips = "".join(
                f'<div class="chip chip-{e["type"].lower()}">{escape(e["title"])}</div>'
                for e in day_events[:2]
            )
            if len(day_events) > 2:
                chips += f'<div class="chip-more">+{len(day_events) - 2} more</div>'
            html += f'<div class="{classes}"><div class="dnum">{day}</div>{chips}</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    # Selected day + month agenda
    left, right = st.columns(2)
    with left:
        st.markdown(f"**{selected:%A, %B} {selected.day}**")
        selected_events = events_by_day.get(selected, [])
        if selected_events:
            st.markdown("".join(event_row(e) for e in selected_events), unsafe_allow_html=True)
        else:
            st.caption("Nothing scheduled.")
    with right:
        st.markdown(f"**{view:%B %Y} agenda**")
        month_events = [e for e in events if (e["date"].year, e["date"].month) == (view.year, view.month)]
        if month_events:
            st.markdown("".join(event_row(e) for e in month_events), unsafe_allow_html=True)
        else:
            st.caption("No gigs or rentals this month.")


# ==========================================
# SESSION STATE
# ==========================================

if "cal_month" not in st.session_state:
    st.session_state.cal_month = today.replace(day=1)

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

# ---------- Right: calendar ----------
with right_col:
    st.subheader("Calendar")

    view = st.session_state.cal_month
    clicked = None

    with st.container(border=True, key="cal_box"):
        prev_col, title_col, next_col = st.columns([1, 4, 1], vertical_alignment="center")
        prev_col.button("‹", key="cal_prev", on_click=shift_month, args=("cal_month", -1), use_container_width=True)
        title_col.markdown(f'<div class="cal-title">{view:%B %Y}</div>', unsafe_allow_html=True)
        next_col.button("›", key="cal_next", on_click=shift_month, args=("cal_month", 1), use_container_width=True)

        # Weekday labels (+ the dot styles for this month's events)
        week_header = (
            '<div class="cal-week">'
            + "".join(f"<div>{w}</div>" for w in ["S", "M", "T", "W", "T", "F", "S"])
            + "</div>"
        )
        st.markdown(week_header + marker_css(view), unsafe_allow_html=True)

        # Day buttons: clicking one opens the detailed calendar
        for week in calendar.Calendar(firstweekday=6).monthdayscalendar(view.year, view.month):
            cols = st.columns(7)
            for col, day in zip(cols, week):
                if day == 0:
                    continue
                d = date(view.year, view.month, day)
                if col.button(str(day), key=f"day_{d:%Y%m%d}", use_container_width=True):
                    clicked = d

        # Legend + next up
        upcoming = [e for e in events if e["date"] >= today][:3]
        footer = (
            '<div class="cal-legend">'
            '<span class="dot dot-gig"></span>Gig'
            '<span class="dot dot-rental"></span>Rental'
            '</div>'
        )
        if upcoming:
            footer += '<div class="next-title">Next up</div>'
            footer += "".join(event_row(e) for e in upcoming)
        st.markdown(footer, unsafe_allow_html=True)

    if clicked:
        st.session_state.dlg_month = clicked.replace(day=1)
        st.session_state.dlg_selected = clicked
        calendar_dialog()