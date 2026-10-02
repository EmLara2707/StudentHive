import calendar
import re
from collections import defaultdict
from datetime import date, timedelta
from html import escape

import streamlit as st

# ---------- Layout sizes (px) ----------
# Tune these to fit your screen. The page itself never scrolls;
# only the boxes below scroll internally if their content is taller.
LIST_H = 650   # left box: rental lists
CAL_H = 680    # left box: calendar (taller than the lists)
TODO_H = 680   # right box: to-do list / rental details
DIVIDER_H = 780  # vertical bar between the left and right sides

# ---------- Page-specific styles ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Montserrat:wght@700;800&display=swap');

    /* ---------- page header (same look as the Marketplace page) ---------- */
    [data-testid="stMain"] p,
    [data-testid="stMain"] button,
    [data-testid="stMain"] input {
        font-family: 'Inter', sans-serif;
    }
    [data-testid="stMain"] .st-key-page_header [data-testid="stMarkdownContainer"] h1 {
        font-family: 'Montserrat', sans-serif;
        font-weight: 800;
        color: #3a3d3f !important;
        padding-bottom: 0;
    }
    [data-testid="stMain"] .st-key-page_header [data-testid="stCaptionContainer"],
    [data-testid="stMain"] .st-key-page_header [data-testid="stCaptionContainer"] * {
        color: rgba(49, 51, 63, 0.6) !important;
    }

    /* ---------- no page scrolling ---------- */
    html, body,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
        overflow: hidden !important;
    }
    [data-testid="stMainBlockContainer"] {
        padding-top: 1.5rem !important;
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
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] .badge.badge {
        color: #FFFFFF !important;
    }

    /* White background */
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stHeader"] {
        background-color: #FFFFFF !important;
    }

    [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #E2E6EA;
    }

    /* ---------- Tabs ---------- */
    [data-testid="stMain"] button[aria-selected="true"] [data-testid="stMarkdownContainer"] p {
        color: #0F9D8A !important;
        font-weight: 700;
    }
    [data-testid="stMain"] [data-baseweb="tab-highlight"] {
        background-color: #0F9D8A !important;
    }

    /* ---------- Filter / view pills ---------- */
    [class*="st-key-pills_"] button {
        border-radius: 999px;
        border: 1.5px solid #3a3d3f;
        background: #ffffff;
        min-height: 1.8rem;
        padding: 0 0.9rem;
    }
    [class*="st-key-pills_"] button[kind="pillsActive"],
    [class*="st-key-pills_"] button[aria-checked="true"] {
        background: #0f6b62;
        border-color: #0f6b62;
    }
    [data-testid="stMain"] [class*="st-key-pills_"] button[kind="pillsActive"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stMain"] [class*="st-key-pills_"] button[aria-checked="true"] [data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
    }

    /* ---------- Sort toggle button (also used by the Back buttons) ---------- */
    [class*="st-key-sort_"] button {
        border-radius: 999px;
        border: 1.5px solid #3a3d3f;
        background: #ffffff;
        min-height: 1.8rem;
        padding: 0 0.9rem;
        box-shadow: none;
    }
    [class*="st-key-sort_"] button:hover {
        background: #E7EDF1;
        border-color: #3a3d3f;
    }
    [class*="st-key-sort_"] button p {
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* ---------- Calendar (my rentals) ---------- */
    [class*="st-key-nav_"] .stButton > button {
        min-height: 2.2rem;
        border: 1px solid #E2E6EA;
        border-radius: 0.6rem;
        background: #F4F6F8;
        box-shadow: none;
    }
    [class*="st-key-nav_"] .stButton > button:hover {
        background: #E7EDF1;
    }
    .cal-title {
        text-align: center;
        font-weight: 800;
        font-size: 1.4rem;
    }
    .dhead {
        text-align: center;
        font-size: 0.9rem;
        font-weight: 700;
        color: #6B7785;
        line-height: 1.4;
    }
    /* Streamlit collapses the weekday row to ~7px, so the first week slides under it.
       Give that first row a real height so every week row starts below the labels. */
    [class*="st-key-calgrid"] > div:first-child {
        min-height: 1.8rem;
    }
    [class*="st-key-calgrid"] { gap: 0.35rem; }
    [class*="st-key-dc_"] {
        position: relative;          /* the invisible click button is stretched over this */
        height: 95px;               /* fixed height, so a cell can never grow into its neighbours */
        min-height: 95px;
        max-height: 95px;
        padding: 0.4rem 0.4rem;
        border-radius: 0.6rem;
        background: #F4F6F8;
        gap: 0.2rem;
        overflow: hidden;            /* nothing can spill into the next day */
        min-width: 0;
        cursor: pointer;
    }
    [class*="st-key-dc_"]:hover { background: #E7EDF1; }
    [class*="st-key-dc_today_"] { box-shadow: inset 0 0 0 2px #0F9D8A; }
    [class*="st-key-dc_"] > div,
    [class*="st-key-dc_"] [data-testid="stMarkdownContainer"] {
        min-width: 0;
        max-width: 100%;
    }
    /* never squash the day number / tags / rows into each other:
       if the calendar is taller than its box, the box scrolls instead */
    [class*="st-key-dc_"] > div:not([class*="st-key-daybtn_"]) {
        flex-shrink: 0 !important;
        height: auto !important;
    }
    [class*="st-key-dc_"] { flex-shrink: 0; }
    [class*="st-key-calgrid"] > div,
    [class*="st-key-calgrid"] [data-testid="stHorizontalBlock"] {
        flex-shrink: 0 !important;
    }
    .dnum {
        font-size: 0.95rem;
        font-weight: 700;
        line-height: 1.1;
    }

    /* invisible button stretched over the whole day cell */
    [class*="st-key-daybtn_"] {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        width: 100% !important;
        height: 100% !important;
        margin: 0;
        z-index: 5;
    }
    [class*="st-key-daybtn_"] > div,
    [class*="st-key-daybtn_"] .stButton {
        width: 100% !important;
        height: 100% !important;
    }
    [class*="st-key-daybtn_"] button {
        width: 100%;
        height: 100%;
        min-height: 100%;
        padding: 0;
        border: none;
        border-radius: 0.6rem;
        background: transparent;
        box-shadow: none;
        cursor: pointer;
    }
    [class*="st-key-daybtn_"] button:hover,
    [class*="st-key-daybtn_"] button:focus:not(:active),
    [class*="st-key-daybtn_"] button:active {
        background: transparent;
        border: none;
        box-shadow: none;
    }
    /* hide the button's own label; the day number is drawn by .dnum underneath */
    [data-testid="stMain"] [class*="st-key-daybtn_"] button [data-testid="stMarkdownContainer"] p {
        opacity: 0;
    }

    /* static (non-clickable) rental labels inside the calendar */
    .chip {
        display: block;
        box-sizing: border-box;
        max-width: 100%;
        padding: 0.1rem 0.45rem;
        margin: 0;
        border-radius: 0.4rem;
        color: #FFFFFF !important;
        font-size: 0.78rem;
        font-weight: 600;
        line-height: 1.4;            /* fixed height per chip */
        flex-shrink: 0;              /* chips never get squashed */
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .chip-renting { background: #0F9D8A; }
    .chip-lending   { background: #F5A03C; }
    .chip-pending   { opacity: 0.55; }

    .chip-more {
        font-size: 0.75rem;
        line-height: 1.4;
        color: #6B7785;
    }

    /* stacks the chips with an even gap under the day number */
    .chip-stack {
        display: flex;
        flex-direction: column;
        gap: 0.2rem;
        margin-top: 0.2rem;
        overflow: hidden;            /* clips anything taller than the cell */
        min-width: 0;
    }
    .cal-legend {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.4rem;
        font-size: 0.9rem;
    }
    .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }
    .dot-renting { background: #0F9D8A; }
    .dot-lending   { background: #F5A03C; margin-left: 0.6rem; }

    /* ---------- Rental cards (clickable) ---------- */
    [class*="st-key-rcard_"] {
        background: #FFFFFF;
        border-radius: 1rem;
        padding: 0 0.9rem 0 0;
        box-shadow: 0 0 12px rgba(0, 0, 0, 0.25);
        gap: 0;
        overflow: hidden;
    }
    [class*="st-key-rcard_"] [data-testid="stHorizontalBlock"] { gap: 0; }
    [class*="st-key-rcard_"] [data-testid="stMarkdownContainer"] { margin: 0; }
    .rc-imgwrap {
        line-height: 0;
        margin: 0;
    }
    .rc-img {
        width: 100%;
        height: 134px;
        object-fit: cover;
        display: block;
        margin: 0;
    }
    [class*="st-key-rcard_"] button {
        background: #0f6b62;
        border: none;
        border-radius: 999px;
        min-height: 2rem;
        padding: 0 1rem;
    }
    [class*="st-key-rcard_"] button:hover,
    [class*="st-key-rcard_"] button:focus:not(:active) {
        background: #0b5750;
        border: none;
    }
    [data-testid="stMain"] [class*="st-key-rcard_"] button [data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .listing-info {
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 0.45rem;
        padding: 0 1rem;
        min-width: 0;
    }
    .listing-name {
        font-weight: 700;
        font-size: 1.05rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .listing-sub {
        font-size: 0.8rem;
        color: #6B7785 !important;
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
    .badge-renting { background: #0F9D8A; }
    .badge-lending   { background: #F5A03C; }
    .badge-pending   { background: #8A94A0; }
    .badge-cancelled { background: #D64545; }
    .listing-price {
        font-weight: 700;
        font-size: 0.9rem;
    }

    /* ---------- Rental details panel ---------- */
    .det-img {
        width: 100%;
        height: 190px;
        object-fit: cover;
        border-radius: 1rem;
        display: block;
        margin-bottom: 0.8rem;
    }
    .det-title {
        font-weight: 800;
        font-size: 1.4rem;
        margin-bottom: 0.4rem;
    }
    .det-badges {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 0.7rem;
    }
    .det-row {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        padding: 0.5rem 0;
        border-bottom: 1px solid #E2E6EA;
        font-size: 0.95rem;
    }
    .det-label { color: #6B7785 !important; }
    .det-value { font-weight: 700; text-align: right; }
    .det-note {
        margin-top: 0.8rem;
        padding: 0.7rem 0.85rem;
        border-radius: 0.75rem;
        background: #F4F6F8;
        font-size: 0.9rem;
        font-weight: 600;
    }
    .det-note-overdue { background: #FBE5E5; }

    /* ---------- To-do panel ---------- */
    .todo-row {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.55rem 0.85rem;
        margin-bottom: 0.5rem;            /* spacing is handled by the clickable container */
        border-radius: 0.75rem;
        background: #F4F6F8;
        border-left: 5px solid #0F9D8A;
    }
    .todo-overdue { border-left-color: #D64545; }
    .todo-soon    { border-left-color: #F5A03C; }
    .todo-info {
        flex: 1;
        min-width: 0;
    }
    .todo-title {
        font-weight: 700;
        font-size: 1rem;
        line-height: 1.3;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .todo-sub {
        font-size: 0.85rem;
        line-height: 1.3;
        color: #6B7785 !important;
    }
    .todo-when {
        font-size: 0.9rem;
        font-weight: 800;
        white-space: nowrap;
    }
    .todo-when-overdue { color: #D64545 !important; }
    .todo-when-soon    { color: #D9822B !important; }

    /* ---------- Vertical divider between left and right sides ---------- */
    .vdivider {
        width: 2px;
        margin: 0 auto;
        border-radius: 999px;
        background: #E2E6EA;
    }

    /* ---------- Clickable to-do rows ---------- */
    [class*="st-key-todo_"] {
        position: relative;              /* the invisible button is stretched over this */
        margin-bottom: 0.5rem;                /* spacing comes from Streamlit's normal gap between elements */
        border-radius: 0.75rem;
        cursor: pointer;
    }
    [class*="st-key-todo_"]:hover .todo-row { background: #E7EDF1; }

    [class*="st-key-todobtn_"] {
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        width: 100% !important;
        height: 100% !important;
        margin: 0;
        z-index: 5;
    }
    [class*="st-key-todobtn_"] > div,
    [class*="st-key-todobtn_"] .stButton {
        width: 100% !important;
        height: 100% !important;
    }
    [class*="st-key-todobtn_"] button {
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
    [class*="st-key-todobtn_"] button:hover,
    [class*="st-key-todobtn_"] button:focus:not(:active),
    [class*="st-key-todobtn_"] button:active {
        background: transparent;
        border: none;
        box-shadow: none;
    }
    [data-testid="stMain"] [class*="st-key-todobtn_"] button [data-testid="stMarkdownContainer"] p {
        opacity: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# SAMPLE DATA (replace with database data later)
# role:      "Renting" (you took an item) / "Lending" (you offered an item)
# status:    "Active" / "Pending" / "Completed" / "Cancelled"
# cancelled_by: "me" / "them" (only for Cancelled)
# ==========================================

today = date.today()
IMG = "https://placehold.co/200"

rentals = [
    # --- My rentals (active / pending) ---
    {"item": "Canon DSLR Camera", "role": "Renting", "status": "Active",
     "start": today - timedelta(days=3), "end": today - timedelta(days=1),
     "price": "₱500/day", "with": "Ana R.", "image": IMG},
    {"item": "Camping Tent (4P)", "role": "Renting", "status": "Active",
     "start": today + timedelta(days=1), "end": today + timedelta(days=4),
     "price": "₱350/day", "with": "Miguel S.", "image": IMG},
    {"item": "Projector", "role": "Lending", "status": "Active",
     "start": today, "end": today + timedelta(days=2),
     "price": "₱400/day", "with": "Carla D.", "image": IMG},
    {"item": "Portable Speaker", "role": "Lending", "status": "Active",
     "start": today + timedelta(days=2), "end": today + timedelta(days=3),
     "price": "₱180/day", "with": "Dan K.", "image": IMG},
    {"item": "Electric Guitar", "role": "Lending", "status": "Pending",
     "start": today + timedelta(days=5), "end": today + timedelta(days=7),
     "price": "₱300/day", "with": "Josh P.", "image": IMG},
    {"item": "Power Drill", "role": "Renting", "status": "Pending",
     "start": today + timedelta(days=9), "end": today + timedelta(days=10),
     "price": "₱150/day", "with": "Leo M.", "image": IMG},
    {"item": "Folding Bike", "role": "Lending", "status": "Active",
     "start": today + timedelta(days=12), "end": today + timedelta(days=15),
     "price": "₱250/day", "with": "Nina T.", "image": IMG},
    # --- Completed ---
    {"item": "Karaoke Set", "role": "Renting", "status": "Completed",
     "start": today - timedelta(days=20), "end": today - timedelta(days=18),
     "price": "₱600/day", "with": "Rico B.", "image": IMG},
    {"item": "Acoustic Guitar", "role": "Lending", "status": "Completed",
     "start": today - timedelta(days=14), "end": today - timedelta(days=11),
     "price": "₱200/day", "with": "Mia L.", "image": IMG},
    {"item": "Tripod Stand", "role": "Renting", "status": "Completed",
     "start": today - timedelta(days=9), "end": today - timedelta(days=8),
     "price": "₱100/day", "with": "Ana R.", "image": IMG},
    # --- Cancelled ---
    {"item": "Sound System", "role": "Renting", "status": "Cancelled", "cancelled_by": "me",
     "start": today - timedelta(days=6), "end": today - timedelta(days=5),
     "price": "₱800/day", "with": "Paolo G.", "image": IMG},
    {"item": "Ring Light", "role": "Lending", "status": "Cancelled", "cancelled_by": "them",
     "start": today - timedelta(days=2), "end": today - timedelta(days=1),
     "price": "₱120/day", "with": "Kyla V.", "image": IMG},
]

# every rental gets an id so a click can say which one was picked
for _i, _r in enumerate(rentals):
    _r["id"] = _i
rentals_by_id = {r["id"]: r for r in rentals}

my_rentals = [r for r in rentals if r["status"] in ("Active", "Pending")]


# ==========================================
# HELPERS
# ==========================================

def fmt_range(r: dict) -> str:
    if r["start"] == r["end"]:
        return f"{r['start']:%b} {r['start'].day}"
    return f"{r['start']:%b} {r['start'].day} – {r['end']:%b} {r['end'].day}"


def plural(n: int, word: str) -> str:
    return f"{n} {word}" + ("" if n == 1 else "s")


def daily_rate(r: dict) -> int:
    m = re.search(r"[\d,]+", r["price"])
    return int(m.group().replace(",", "")) if m else 0


def badges_html(r: dict) -> str:
    out = f'<span class="badge badge-{r["role"].lower()}">{escape(r["role"])}</span>'
    if r["status"] == "Pending":
        out += '<span class="badge badge-pending">Pending</span>'
    if r["status"] == "Cancelled":
        who = "by you" if r["cancelled_by"] == "me" else "by them"
        out += f'<span class="badge badge-cancelled">Cancelled {who}</span>'
    return out


def card_info_html(r: dict) -> str:
    """Single-line HTML (no indentation, so Markdown doesn't treat it as code)."""
    who_label = "From" if r["role"] == "Renting" else "To"
    return (
        '<div class="listing-info">'
        f'<div class="listing-name">{escape(r["item"])}</div>'
        f'<div class="listing-sub">{fmt_range(r)} · {who_label} {escape(r["with"])}</div>'
        f'<div class="listing-meta">{badges_html(r)}'
        f'<span class="listing-price">{escape(r["price"])}</span></div>'
        '</div>'
    )


# ----- selection (which rental / day is shown) -----

def open_rental(rid: int) -> None:
    st.session_state.selected_rental = rid


def close_rental() -> None:
    st.session_state.selected_rental = None


def open_day(d: date) -> None:
    st.session_state.selected_day = d
    st.session_state.selected_rental = None


def close_day() -> None:
    st.session_state.selected_day = None
    st.session_state.selected_rental = None


def render_cards(items: list, tab: str) -> None:
    """Each card is a real container with a View button, so it is clickable."""
    for r in items:
        with st.container(key=f"rcard_{tab}_{r['id']}"):
            img_col, info_col, btn_col = st.columns([1.4, 6, 1.6], vertical_alignment="center")
            img_col.markdown(
                f'<div class="rc-imgwrap"><img class="rc-img" src="{escape(r["image"])}"></div>',
                unsafe_allow_html=True,
            )
            info_col.markdown(card_info_html(r), unsafe_allow_html=True)
            btn_col.button("View", key=f"view_{tab}_{r['id']}", on_click=open_rental,
                           args=(r["id"],), use_container_width=True)


# ----- calendar / month navigation -----

def shift_month(key: str, delta: int) -> None:
    m = st.session_state[key]
    idx = m.year * 12 + (m.month - 1) + delta
    st.session_state[key] = date(idx // 12, idx % 12 + 1, 1)


def go_today(key: str) -> None:
    st.session_state[key] = date.today().replace(day=1)


def render_calendar(view: date, items: list) -> None:
    # Expand every rental across the days it covers
    by_day = defaultdict(list)
    for r in items:
        d = r["start"]
        while d <= r["end"]:
            by_day[d].append(r)
            d += timedelta(days=1)

    with st.container(key="calgrid"):
        head = st.columns(7, gap="small")
        for col, n in zip(head, ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]):
            col.markdown(f'<div class="dhead">{n}</div>', unsafe_allow_html=True)

        for week in calendar.Calendar(firstweekday=6).monthdayscalendar(view.year, view.month):
            cols = st.columns(7, gap="small")
            for col, day in zip(cols, week):
                if day == 0:
                    continue
                d = date(view.year, view.month, day)
                day_items = by_day.get(d, [])
                cell_key = f"dc_today_{d:%Y%m%d}" if d == today else f"dc_{d:%Y%m%d}"
                with col:
                    with st.container(key=cell_key):
                        # invisible button covering the whole cell -> opens the day view
                        st.button(str(day), key=f"daybtn_{d:%Y%m%d}",
                                  on_click=open_day, args=(d,))

                        # day number + chips go in ONE element so they can't collapse into each other
                        chips = "".join(
                            f'<div class="chip chip-{r["role"].lower()}'
                            f'{" chip-pending" if r["status"] == "Pending" else ""}">'
                            f'{escape(r["item"])}</div>'
                            for r in day_items[:2]
                        )
                        if len(day_items) > 2:
                            chips += f'<div class="chip-more">+{len(day_items) - 2} more</div>'
                        st.markdown(
                            f'<div class="dnum">{day}</div><div class="chip-stack">{chips}</div>',
                            unsafe_allow_html=True,
                        )


def render_day_view(d: date, items: list) -> None:
    """Expanded view of one calendar day, shown inside the calendar box."""
    day_items = [r for r in items if r["start"] <= d <= r["end"]]
    day_items.sort(key=lambda r: r["start"])

    st.button("← Back to calendar", key="sort_dayback", on_click=close_day)
    st.markdown(
        f'<div class="cal-title" style="text-align:left">{d:%A, %B} {d.day}, {d.year}</div>',
        unsafe_allow_html=True,
    )
    st.caption(f"{plural(len(day_items), 'rental')} on this day" if day_items
               else "Nothing scheduled for this day.")
    if day_items:
        render_cards(day_items, "day")


# ----- sorting -----

def toggle_sort(tab: str) -> None:
    st.session_state[f"asc_{tab}"] = not st.session_state[f"asc_{tab}"]


def sort_button(tab: str, asc_label: str, desc_label: str) -> None:
    """A button that just flips the order (no dropdown)."""
    asc = st.session_state[f"asc_{tab}"]
    st.button(
        asc_label if asc else desc_label,
        key=f"sort_{tab}",
        on_click=toggle_sort,
        args=(tab,),
        use_container_width=True,
    )


# ----- to-do list -----

def build_todos() -> list:
    """Most urgent things first: overdue, then soonest due.
    Each entry is (due date, title, subtitle, rental id)."""
    todos = []
    for r in my_rentals:
        item = r["item"]
        rid = r["id"]
        if r["status"] == "Pending":
            if r["role"] == "Lending":
                todos.append((r["start"], f"Respond to request: {item}",
                              f"{r['with']} wants to rent it", rid))
            continue
        if r["role"] == "Renting":
            if r["start"] >= today:
                todos.append((r["start"], f"Pick up {item}", f"From {r['with']}", rid))
            todos.append((r["end"], f"Return {item}", f"To {r['with']}", rid))
        else:
            if r["start"] >= today:
                todos.append((r["start"], f"Hand over {item}", f"To {r['with']}", rid))
            todos.append((r["end"], f"Collect {item} back", f"From {r['with']}", rid))
    todos.sort(key=lambda t: t[0])
    return todos


def todo_row(due: date, title: str, sub: str) -> str:
    days = (due - today).days
    if days < 0:
        when, level = f"Overdue {-days}d", "overdue"
    elif days == 0:
        when, level = "Today", "soon"
    elif days == 1:
        when, level = "Tomorrow", "soon"
    else:
        when, level = f"In {days} days", ""
    row_cls = f"todo-{level}" if level else ""
    when_cls = f"todo-when-{level}" if level else ""
    return (
        f'<div class="todo-row {row_cls}">'
        '<div class="todo-info">'
        f'<div class="todo-title">{escape(title)}</div>'
        f'<div class="todo-sub">{escape(sub)} · {due:%b} {due.day}</div>'
        '</div>'
        f'<div class="todo-when {when_cls}">{when}</div>'
        '</div>'
    )


def render_todos(todos: list) -> None:
    """Each to-do is a container with an invisible button over the whole row."""
    for i, (due, title, sub, rid) in enumerate(todos):
        with st.container(key=f"todo_{i}_{rid}"):
            st.button("Open", key=f"todobtn_{i}_{rid}", on_click=open_rental, args=(rid,))
            st.markdown(todo_row(due, title, sub), unsafe_allow_html=True)


# ----- details panel -----

def detail_html(r: dict) -> str:
    days = (r["end"] - r["start"]).days + 1
    rate = daily_rate(r)
    renting = r["role"] == "Renting"

    note_cls = ""
    if r["status"] == "Cancelled":
        note = "Cancelled by you." if r["cancelled_by"] == "me" else f"Cancelled by {r['with']}."
    elif r["status"] == "Completed":
        note = "This rental was completed."
    elif r["status"] == "Pending":
        note = (f"Waiting for {r['with']} to approve your request." if renting
                else f"{r['with']} is waiting for your response.")
    elif today < r["start"]:
        note = f"Starts in {plural((r['start'] - today).days, 'day')}."
    elif today <= r["end"]:
        left = (r["end"] - today).days
        note = "In progress — ends today." if left == 0 else f"In progress — ends in {plural(left, 'day')}."
    else:
        note = f"Overdue by {plural((today - r['end']).days, 'day')}."
        note_cls = " det-note-overdue"

    rows = [
        ("Dates", fmt_range(r)),
        ("Duration", plural(days, "day")),
        ("Rate", r["price"]),
        ("Estimated total", f"₱{rate * days:,}"),
        ("Owner" if renting else "Renter", r["with"]),
        ("Your role", "Renting this item" if renting else "Lending this item"),
    ]
    rows_html = "".join(
        f'<div class="det-row"><span class="det-label">{label}</span>'
        f'<span class="det-value">{escape(value)}</span></div>'
        for label, value in rows
    )
    return (
        f'<img class="det-img" src="{escape(r["image"])}">'
        f'<div class="det-title">{escape(r["item"])}</div>'
        f'<div class="det-badges">{badges_html(r)}</div>'
        f'{rows_html}'
        f'<div class="det-note{note_cls}">{escape(note)}</div>'
    )


# ==========================================
# SESSION STATE
# ==========================================

if "rent_month" not in st.session_state:
    st.session_state.rent_month = today.replace(day=1)

# True = oldest/soonest first, False = newest/latest first
st.session_state.setdefault("asc_mine", True)
st.session_state.setdefault("asc_done", False)
st.session_state.setdefault("asc_cancel", False)
st.session_state.setdefault("selected_rental", None)  # id shown in the details panel
st.session_state.setdefault("selected_day", None)     # day shown in the expanded calendar view


# ==========================================
# PAGE
# ==========================================

with st.container(key="page_header"):
    st.title("Rentals")
    st.caption("Manage and track your rentals and review past transactions.")

left_col, divider_col, right_col = st.columns([2, 0.06, 1], gap="small")

with divider_col:
    st.markdown(
        f'<div class="vdivider" style="height:{DIVIDER_H}px"></div>',
        unsafe_allow_html=True,
    )

# ---------- Left: tabs ----------
with left_col:
    tab_mine, tab_done, tab_cancel = st.tabs(["My Rentals", "Completed", "Cancelled"])

    # ----- My Rentals: calendar or list -----
    with tab_mine:
        view_col, filt_col, sort_col = st.columns([2, 3, 2], vertical_alignment="center")
        with view_col:
            view_mode = st.pills(
                "View", ["Calendar", "List"], default="Calendar",
                label_visibility="collapsed", key="pills_view",
            ) or "Calendar"
        with filt_col:
            chosen = st.pills(
                "Filter", ["Renting", "Lending"], selection_mode="multi",
                label_visibility="collapsed", key="pills_mine",
            ) or []

        # none or both selected -> show everything
        items = [r for r in my_rentals if len(chosen) != 1 or r["role"] == chosen[0]]

        if view_mode == "Calendar":
            view = st.session_state.rent_month
            with st.container(height=CAL_H, border=True):
                if st.session_state.selected_day is not None:
                    render_day_view(st.session_state.selected_day, items)
                else:
                    with st.container(key="nav_mine"):
                        prev_col, title_col, next_col, today_col = st.columns(
                            [1, 4, 1, 2], vertical_alignment="center"
                        )
                        prev_col.button("‹", key="rent_prev", on_click=shift_month,
                                        args=("rent_month", -1), use_container_width=True)
                        title_col.markdown(f'<div class="cal-title">{view:%B %Y}</div>', unsafe_allow_html=True)
                        next_col.button("›", key="rent_next", on_click=shift_month,
                                        args=("rent_month", 1), use_container_width=True)
                        today_col.button("Today", key="rent_today", on_click=go_today,
                                         args=("rent_month",), use_container_width=True)

                    render_calendar(view, items)
                    st.markdown(
                        '<div class="cal-legend">'
                        '<span class="dot dot-renting"></span>Renting (rentals you took)'
                        '<span class="dot dot-lending"></span>Lending (rentals you offered)'
                        '</div>',
                        unsafe_allow_html=True,
                    )
        else:
            with sort_col:
                sort_button("mine", "↑ Soonest first", "↓ Latest first")
            items.sort(key=lambda r: r["start"], reverse=not st.session_state.asc_mine)
            with st.container(height=LIST_H, border=True):
                if items:
                    render_cards(items, "mine")
                else:
                    st.caption("No rentals to show.")

    # ----- Completed: list only -----
    with tab_done:
        filt_col, sort_col = st.columns([5, 2], vertical_alignment="center")
        with filt_col:
            chosen = st.pills(
                "Filter", ["Items I rented", "Items I rented out"], selection_mode="multi",
                label_visibility="collapsed", key="pills_done",
            ) or []
        with sort_col:
            sort_button("done", "↑ Oldest first", "↓ Newest first")

        role_map = {"Items I rented": "Renting", "Items I rented out": "Lending"}
        items = [r for r in rentals if r["status"] == "Completed"
                 and (len(chosen) != 1 or r["role"] == role_map[chosen[0]])]
        items.sort(key=lambda r: r["end"], reverse=not st.session_state.asc_done)

        with st.container(height=LIST_H, border=True):
            if items:
                render_cards(items, "done")
            else:
                st.caption("No completed rentals.")

    # ----- Cancelled: list only -----
    with tab_cancel:
        filt_col, sort_col = st.columns([5, 2], vertical_alignment="center")
        with filt_col:
            chosen = st.pills(
                "Filter", ["Cancelled by me", "Cancelled by others"], selection_mode="multi",
                label_visibility="collapsed", key="pills_cancel",
            ) or []
        with sort_col:
            sort_button("cancel", "↑ Oldest first", "↓ Newest first")

        who_map = {"Cancelled by me": "me", "Cancelled by others": "them"}
        items = [r for r in rentals if r["status"] == "Cancelled"
                 and (len(chosen) != 1 or r["cancelled_by"] == who_map[chosen[0]])]
        items.sort(key=lambda r: r["start"], reverse=not st.session_state.asc_cancel)

        with st.container(height=LIST_H, border=True):
            if items:
                render_cards(items, "cancel")
            else:
                st.caption("No cancelled rentals.")

# ---------- Right: rental details (replaces the to-do list) or to-do summary ----------
with right_col:
    selected = rentals_by_id.get(st.session_state.selected_rental)

    if selected is not None:
        st.subheader("Rental Details")
        st.caption("Press Back to return to your to-do list.")
        with st.container(height=TODO_H, border=True):
            # the "sort_" key prefix reuses the pill-button style
            st.button("← Back to To-Do", key="sort_back", on_click=close_rental)
            st.markdown(detail_html(selected), unsafe_allow_html=True)
    else:
        st.subheader("To-Do")
        todos = build_todos()
        overdue = sum(1 for t in todos if t[0] < today)
        st.caption(
            f"{len(todos)} open task(s)" + (f" · {overdue} overdue" if overdue else "")
        )

        with st.container(height=TODO_H, border=True):
            if todos:
                render_todos(todos)
            else:
                st.caption("You're all caught up.")