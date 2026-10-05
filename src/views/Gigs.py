import calendar
import re
from collections import defaultdict
from datetime import date, timedelta
from html import escape

import streamlit as st

# ---------- Layout sizes (px) ----------
# Tune these to fit your screen. The page itself never scrolls;
# only the boxes below scroll internally if their content is taller.
LIST_H = 680   # left box: gig lists
CAL_H = 680    # left box: calendar (taller than the lists)
TODO_H = 680   # right box: to-do list / gig details
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
    [data-testid="stMain"] [data-testid="stTab"] {
        background: transparent;
    }

    /* unselected tab text: same ink color as the page text */
    [data-testid="stMain"] [data-testid="stTab"] [data-testid="stMarkdownContainer"] p {
        color: #3a3d3f !important;
        font-weight: 600;
    }

    /* hover */
    [data-testid="stMain"] [data-testid="stTab"]:hover [data-testid="stMarkdownContainer"] p {
        color: #0f6b62 !important;
    }

    /* selected tab text */
    [data-testid="stMain"] [data-testid="stTab"][aria-selected="true"] [data-testid="stMarkdownContainer"] p {
        color: #0f6b62 !important;
        font-weight: 700;
    }

    /* underline under the selected tab */
    [data-testid="stMain"] [data-testid="stTab"] .react-aria-SelectionIndicator,
    [data-testid="stMain"] [data-baseweb="tab-highlight"] {
        background-color: #0f6b62 !important;
    }

    /* ---------- Filter / view pills (same look as Marketplace Gig / Rentals) ---------- */
    [class*="st-key-pills_"] button {
        border-radius: 999px;
        border: 1.5px solid #3a3d3f;
        background: #ffffff;
        min-height: 1.8rem;
        padding: 0 0.9rem;
        box-shadow: none;
    }
    [data-testid="stMain"] [class*="st-key-pills_"] button [data-testid="stMarkdownContainer"] p {
        color: #3a3d3f !important;
    }

    /* hover: teal outline + teal text */
    [class*="st-key-pills_"] button:hover {
        border-color: #0f6b62;
        background: #ffffff;
    }
    [data-testid="stMain"] [class*="st-key-pills_"] button:hover [data-testid="stMarkdownContainer"] p {
        color: #0f6b62 !important;
    }

    /* selected: solid teal with white text */
    [class*="st-key-pills_"] [data-testid="stBaseButton-pillsActive"],
    [class*="st-key-pills_"] button[kind="pillsActive"],
    [class*="st-key-pills_"] button[aria-pressed="true"],
    [class*="st-key-pills_"] button[aria-checked="true"] {
        background: #0f6b62 !important;
        border-color: #0f6b62 !important;
    }
    [data-testid="stMain"] [class*="st-key-pills_"] [data-testid="stBaseButton-pillsActive"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stMain"] [class*="st-key-pills_"] button[kind="pillsActive"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stMain"] [class*="st-key-pills_"] button[aria-pressed="true"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stMain"] [class*="st-key-pills_"] button[aria-checked="true"] [data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
    }
    [class*="st-key-pills_"] [data-testid="stBaseButton-pillsActive"]:hover,
    [class*="st-key-pills_"] button[kind="pillsActive"]:hover {
        background: #0b5750 !important;
        border-color: #0b5750 !important;
    }

    /* focus ring after clicking (replaces Streamlit's default red) */
    [class*="st-key-pills_"] button:focus,
    [class*="st-key-pills_"] button:focus-visible {
        outline: none;
        box-shadow: 0 0 0 0.15rem rgba(15, 107, 98, 0.25) !important;
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

    /* ---------- Calendar (my gigs) ---------- */
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
    [class*="st-key-calgrid"] { gap: 0.8rem; }
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

    /* static (non-clickable) gig labels inside the calendar */
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
    .chip-doing { background: #0F9D8A; }
    .chip-hiring    { background: #F5A03C; }
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
    .dot-doing { background: #0F9D8A; }
    .dot-hiring    { background: #F5A03C; margin-left: 0.6rem; }

    /* ---------- Gig cards (clickable) ---------- */
    [class*="st-key-rcard_"] {
        background: #FFFFFF;
        border-radius: 1rem;
        padding: 0 0.9rem 0 0;
        box-shadow: 0 2px 12px rgba(27, 42, 65, 0.14);
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
    .badge-doing { background: #0F9D8A; }
    .badge-hiring    { background: #F5A03C; }
    .badge-pending   { background: #8A94A0; }
    .badge-cancelled { background: #D64545; }
    .listing-price {
        font-weight: 700;
        font-size: 0.9rem;
    }

    /* ---------- Gig details panel ---------- */
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

    /* ---------- Action buttons in the details panel ---------- */
    /* Accept / Complete: solid teal */
    [class*="st-key-act_accept"] button,
    [class*="st-key-act_complete"] button {
        background: #0f6b62;
        border: none;
        border-radius: 999px;
        min-height: 2.3rem;
        padding: 0 1rem;
        box-shadow: none;
    }
    [class*="st-key-act_accept"] button:hover,
    [class*="st-key-act_accept"] button:focus:not(:active),
    [class*="st-key-act_complete"] button:hover,
    [class*="st-key-act_complete"] button:focus:not(:active) {
        background: #0b5750;
        border: none;
    }
    [data-testid="stMain"] [class*="st-key-act_accept"] button [data-testid="stMarkdownContainer"] p,
    [data-testid="stMain"] [class*="st-key-act_complete"] button [data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
        font-weight: 600;
        font-size: 0.9rem;
    }

    /* Reject / Cancel: white with a red outline */
    [class*="st-key-act_reject"] button,
    [class*="st-key-act_cancel"] button {
        background: #FFFFFF;
        border: 1.5px solid #D64545;
        border-radius: 999px;
        min-height: 2.3rem;
        padding: 0 1rem;
        box-shadow: none;
    }
    [class*="st-key-act_reject"] button:hover,
    [class*="st-key-act_reject"] button:focus:not(:active),
    [class*="st-key-act_cancel"] button:hover,
    [class*="st-key-act_cancel"] button:focus:not(:active) {
        background: #FBE5E5;
        border: 1.5px solid #D64545;
    }
    [data-testid="stMain"] [class*="st-key-act_reject"] button [data-testid="stMarkdownContainer"] p,
    [data-testid="stMain"] [class*="st-key-act_cancel"] button [data-testid="stMarkdownContainer"] p {
        color: #D64545 !important;
        font-weight: 600;
        font-size: 0.9rem;
    }

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
# role:      "Doing" (you do the gig for someone) / "Hiring" (you posted a gig for someone to do)
# status:    "Active" / "Pending" / "Completed" / "Cancelled"
# cancelled_by: "me" / "them" (only for Cancelled)
#
# Pending + Hiring = someone wants to take YOUR gig (you can accept / reject)
# Pending + Doing  = YOU offered to do someone's gig (waiting for their answer)
# ==========================================

today = date.today()
IMG = "https://placehold.co/200"


def _sample_gigs() -> list:
    return [
        # --- Active ---
        {"item": "Math Tutoring (Calculus)", "role": "Doing", "status": "Active",
         "start": today - timedelta(days=3), "end": today - timedelta(days=1),
         "price": "₱500/day", "with": "Ana R.", "image": IMG},
        {"item": "Event Photography", "role": "Doing", "status": "Active",
         "start": today + timedelta(days=1), "end": today + timedelta(days=4),
         "price": "₱1,200/day", "with": "Miguel S.", "image": IMG},
        {"item": "Poster Design", "role": "Hiring", "status": "Active",
         "start": today, "end": today + timedelta(days=2),
         "price": "₱400/day", "with": "Carla D.", "image": IMG},
        {"item": "Thesis Proofreading", "role": "Hiring", "status": "Active",
         "start": today + timedelta(days=2), "end": today + timedelta(days=3),
         "price": "₱300/day", "with": "Dan K.", "image": IMG},
        {"item": "Dog Walking", "role": "Doing", "status": "Active",
         "start": today + timedelta(days=12), "end": today + timedelta(days=15),
         "price": "₱250/day", "with": "Nina T.", "image": IMG},
        # --- Pending (not accepted yet) ---
        {"item": "Guitar Lessons", "role": "Hiring", "status": "Pending",
         "start": today + timedelta(days=5), "end": today + timedelta(days=7),
         "price": "₱350/day", "with": "Josh P.", "image": IMG},
        {"item": "Resume Review", "role": "Hiring", "status": "Pending",
         "start": today + timedelta(days=3), "end": today + timedelta(days=4),
         "price": "₱400/day", "with": "Sam W.", "image": IMG},
        {"item": "Python Tutoring", "role": "Doing", "status": "Pending",
         "start": today + timedelta(days=9), "end": today + timedelta(days=10),
         "price": "₱450/day", "with": "Leo M.", "image": IMG},
        # --- Completed ---
        {"item": "Video Editing", "role": "Doing", "status": "Completed",
         "start": today - timedelta(days=20), "end": today - timedelta(days=18),
         "price": "₱800/day", "with": "Rico B.", "image": IMG},
        {"item": "Logo Design", "role": "Hiring", "status": "Completed",
         "start": today - timedelta(days=14), "end": today - timedelta(days=11),
         "price": "₱600/day", "with": "Mia L.", "image": IMG},
        {"item": "Essay Editing", "role": "Doing", "status": "Completed",
         "start": today - timedelta(days=9), "end": today - timedelta(days=8),
         "price": "₱200/day", "with": "Ana R.", "image": IMG},
        # --- Cancelled ---
        {"item": "Wedding Videography", "role": "Doing", "status": "Cancelled", "cancelled_by": "me",
         "start": today - timedelta(days=6), "end": today - timedelta(days=5),
         "price": "₱1,500/day", "with": "Paolo G.", "image": IMG},
        {"item": "Social Media Management", "role": "Hiring", "status": "Cancelled", "cancelled_by": "them",
         "start": today - timedelta(days=2), "end": today - timedelta(days=1),
         "price": "₱350/day", "with": "Kyla V.", "image": IMG},
    ]


# Kept in session_state so accepting / rejecting / completing / cancelling sticks between reruns.
# TODO: replace with your database; the update_gig() function below is where to save changes.
if "gigs" not in st.session_state:
    _data = _sample_gigs()
    for _i, _r in enumerate(_data):
        _r["id"] = _i          # every gig gets an id so a click can say which one was picked
    st.session_state.gigs = _data

gigs = st.session_state.gigs
gigs_by_id = {r["id"]: r for r in gigs}

my_gigs = [r for r in gigs if r["status"] == "Active"]                        # calendar + My Gigs list
open_gigs = [r for r in gigs if r["status"] in ("Active", "Pending")]          # to-do list


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
    who_label = "For" if r["role"] == "Doing" else "By"
    return (
        '<div class="listing-info">'
        f'<div class="listing-name">{escape(r["item"])}</div>'
        f'<div class="listing-sub">{fmt_range(r)} · {who_label} {escape(r["with"])}</div>'
        f'<div class="listing-meta">{badges_html(r)}'
        f'<span class="listing-price">{escape(r["price"])}</span></div>'
        '</div>'
    )


# ----- changing a gig's status -----

def get_gig(rid: int) -> dict:
    return next(r for r in st.session_state.gigs if r["id"] == rid)


def update_gig(rid: int, status: str, cancelled_by: str | None = None, msg: str = "") -> None:
    """Accept / reject / complete / cancel all go through here."""
    r = get_gig(rid)
    r["status"] = status
    if cancelled_by:
        r["cancelled_by"] = cancelled_by
    if msg:
        st.session_state.toast = msg
    # TODO: save the new status in your backend here


@st.dialog("Reject this request?")
def confirm_reject_dialog(rid: int) -> None:
    r = get_gig(rid)
    st.write(f"{r['with']}'s request to take “{r['item']}” will be declined.")
    c1, c2 = st.columns(2)
    if c1.button("Keep request", key="dlg_reject_no", use_container_width=True):
        st.rerun()
    if c2.button("Yes, reject", key="dlg_reject_yes", type="primary", use_container_width=True):
        update_gig(rid, "Cancelled", "me", f"Rejected request for {r['item']}")
        st.rerun()


@st.dialog("Cancel this gig?")
def confirm_cancel_dialog(rid: int) -> None:
    r = get_gig(rid)
    st.write(f"“{r['item']}” with {r['with']} will be cancelled. This can’t be undone.")
    c1, c2 = st.columns(2)
    if c1.button("Keep gig", key="dlg_cancel_no", use_container_width=True):
        st.rerun()
    if c2.button("Yes, cancel it", key="dlg_cancel_yes", type="primary", use_container_width=True):
        update_gig(rid, "Cancelled", "me", f"Cancelled {r['item']}")
        st.rerun()

@st.dialog("Cancel this request?")
def confirm_cancel_request_dialog(rid: int) -> None:
    r = get_gig(rid)
    st.write(f"Your offer to do “{r['item']}” for {r['with']} will be withdrawn.")
    c1, c2 = st.columns(2)
    if c1.button("Keep request", key="dlg_creq_no", use_container_width=True):
        st.rerun()
    if c2.button("Yes, cancel it", key="dlg_creq_yes", type="primary", use_container_width=True):
        update_gig(rid, "Cancelled", "me", f"Cancelled request for {r['item']}")
        st.rerun()

# ----- selection (which gig / day is shown) -----

def open_gig(rid: int) -> None:
    st.session_state.selected_gig = rid


def close_gig() -> None:
    st.session_state.selected_gig = None


def open_day(d: date) -> None:
    st.session_state.selected_day = d
    st.session_state.selected_gig = None


def close_day() -> None:
    st.session_state.selected_day = None
    st.session_state.selected_gig = None


def render_cards(items: list, tab: str, top_pad: bool = True) -> None:
    """Each card is a real container with a View button, so it is clickable."""
    if top_pad:
        st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
    for r in items:
        with st.container(key=f"rcard_{tab}_{r['id']}"):
            img_col, info_col, btn_col = st.columns([1.4, 6, 1.6], vertical_alignment="center")
            img_col.markdown(
                f'<div class="rc-imgwrap"><img class="rc-img" src="{escape(r["image"])}"></div>',
                unsafe_allow_html=True,
            )
            info_col.markdown(card_info_html(r), unsafe_allow_html=True)
            btn_col.button("View", key=f"view_{tab}_{r['id']}", on_click=open_gig,
                           args=(r["id"],), use_container_width=True)


# ----- calendar / month navigation -----

def shift_month(key: str, delta: int) -> None:
    m = st.session_state[key]
    idx = m.year * 12 + (m.month - 1) + delta
    st.session_state[key] = date(idx // 12, idx % 12 + 1, 1)


def go_today(key: str) -> None:
    st.session_state[key] = date.today().replace(day=1)


def render_calendar(view: date, items: list) -> None:
    # Expand every gig across the days it covers
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
    st.caption(f"{plural(len(day_items), 'gig')} on this day" if day_items
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
    Each entry is (due date, title, subtitle, gig id)."""
    todos = []
    for r in open_gigs:
        item = r["item"]
        rid = r["id"]
        if r["status"] == "Pending":
            if r["role"] == "Hiring":
                todos.append((r["start"], f"Respond to applicant: {item}",
                              f"{r['with']} wants to take this gig", rid))
            continue
        if r["role"] == "Doing":
            if r["start"] >= today:
                todos.append((r["start"], f"Start {item}", f"For {r['with']}", rid))
            todos.append((r["end"], f"Deliver {item}", f"To {r['with']}", rid))
        else:
            if r["start"] >= today:
                todos.append((r["start"], f"{item} begins", f"By {r['with']}", rid))
            todos.append((r["end"], f"Review & pay for {item}", f"To {r['with']}", rid))
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
            st.button("Open", key=f"todobtn_{i}_{rid}", on_click=open_gig, args=(rid,))
            st.markdown(todo_row(due, title, sub), unsafe_allow_html=True)


# ----- details panel -----

def detail_html(r: dict) -> str:
    days = (r["end"] - r["start"]).days + 1
    rate = daily_rate(r)
    doing = r["role"] == "Doing"

    note_cls = ""
    if r["status"] == "Cancelled":
        note = "Cancelled by you." if r["cancelled_by"] == "me" else f"Cancelled by {r['with']}."
    elif r["status"] == "Completed":
        note = "This gig was completed."
    elif r["status"] == "Pending":
        note = (f"Waiting for {r['with']} to accept your offer." if doing
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
        ("Client" if doing else "Student", r["with"]),
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


def render_actions(r: dict) -> None:
    """Buttons under the details, depending on status and whether the gig has started."""
    rid = r["id"]

    # Someone asked to take MY gig -> I decide
    if r["status"] == "Pending" and r["role"] == "Hiring":
        c1, c2 = st.columns(2)
        c1.button(
            "Accept", key="act_accept", on_click=update_gig,
            args=(rid, "Active", None, f"Accepted {r['with']}'s request for {r['item']}"),
            use_container_width=True,
        )
        if c2.button("Reject", key="act_reject", use_container_width=True):
            confirm_reject_dialog(rid)

    # I offered to do someone's gig and they haven't answered -> I can withdraw it
    elif r["status"] == "Pending" and r["role"] == "Doing":
        if st.button("Cancel request", key="act_cancel", use_container_width=True):
            confirm_cancel_request_dialog(rid)

    elif r["status"] == "Active":
        if today >= r["start"]:
            # already started -> can be completed or cancelled
            c1, c2 = st.columns(2)
            c1.button(
                "Complete", key="act_complete", on_click=update_gig,
                args=(rid, "Completed", None, f"Marked {r['item']} as completed"),
                use_container_width=True,
            )
            if c2.button("Cancel", key="act_cancel", use_container_width=True):
                confirm_cancel_dialog(rid)
        else:
            # hasn't begun yet -> can only be cancelled
            if st.button("Cancel", key="act_cancel", use_container_width=True):
                confirm_cancel_dialog(rid)


# ==========================================
# SESSION STATE
# ==========================================

if "gig_month" not in st.session_state:
    st.session_state.gig_month = today.replace(day=1)

# True = oldest/soonest first, False = newest/latest first
st.session_state.setdefault("asc_mine", True)
st.session_state.setdefault("asc_pending", True)
st.session_state.setdefault("asc_done", False)
st.session_state.setdefault("asc_cancel", False)
st.session_state.setdefault("selected_gig", None)   # id shown in the details panel
st.session_state.setdefault("selected_day", None)   # day shown in the expanded calendar view


# ==========================================
# PAGE
# ==========================================

if "toast" in st.session_state:
    st.toast(st.session_state.pop("toast"))

with st.container(key="page_header"):
    st.title("Gigs")
    st.caption("Manage and track your gigs and review past transactions.")

left_col, divider_col, right_col = st.columns([2, 0.06, 1], gap="small")

with divider_col:
    st.markdown(
        f'<div class="vdivider" style="height:{DIVIDER_H}px"></div>',
        unsafe_allow_html=True,
    )

# ---------- Left: tabs ----------
with left_col:
    tab_mine, tab_pending, tab_done, tab_cancel = st.tabs(
        ["My Gigs", "Pending", "Completed", "Cancelled"]
    )

    # ----- My Gigs: calendar or list (active gigs only) -----
    with tab_mine:
        view_col, filt_col, _, sort_col = st.columns([1.1, 1.9, 1.7, 1.3], vertical_alignment="center")
        with view_col:
            view_mode = st.pills(
                "View", ["Calendar", "List"], default="Calendar",
                label_visibility="collapsed", key="pills_view",
            ) or "Calendar"
        with filt_col:
            chosen = st.pills(
                "Filter", ["Doing", "Hiring"], selection_mode="single",
                label_visibility="collapsed", key="pills_mine",
            )

        # nothing selected -> show everything
        items = [r for r in my_gigs if chosen is None or r["role"] == chosen]

        if view_mode == "Calendar":
            view = st.session_state.gig_month
            with st.container(height=CAL_H, border=False):
                if st.session_state.selected_day is not None:
                    render_day_view(st.session_state.selected_day, items)
                else:
                    with st.container(key="nav_mine"):
                        prev_col, title_col, next_col, today_col = st.columns(
                            [1, 4, 1, 2], vertical_alignment="center"
                        )
                        prev_col.button("‹", key="gig_prev", on_click=shift_month,
                                        args=("gig_month", -1), use_container_width=True)
                        title_col.markdown(f'<div class="cal-title">{view:%B %Y}</div>', unsafe_allow_html=True)
                        next_col.button("›", key="gig_next", on_click=shift_month,
                                        args=("gig_month", 1), use_container_width=True)
                        today_col.button("Today", key="gig_today", on_click=go_today,
                                         args=("gig_month",), use_container_width=True)

                    render_calendar(view, items)
                    st.markdown(
                        '<div class="cal-legend">'
                        '<span class="dot dot-doing"></span>Doing (gigs you took)'
                        '<span class="dot dot-hiring"></span>Hiring (gigs you offered)'
                        '</div>',
                        unsafe_allow_html=True,
                    )
        else:
            with sort_col:
                sort_button("mine", "↑ Soonest first", "↓ Latest first")
            items.sort(key=lambda r: r["start"], reverse=not st.session_state.asc_mine)
            with st.container(height=LIST_H, border=False):
                if items:
                    render_cards(items, "mine")
                else:
                    st.caption("No gigs to show.")

    # ----- Pending: requests that haven't been accepted yet -----
    with tab_pending:
        filt_col, sort_col = st.columns([4.726, 1.274], vertical_alignment="center")
        with filt_col:
            chosen = st.pills(
                "Filter", ["Requests to me", "Requests I sent"], selection_mode="single",
                label_visibility="collapsed", key="pills_pending",
            )
        with sort_col:
            sort_button("pending", "↑ Soonest first", "↓ Latest first")

        # "Requests to me" = someone wants to take my gig (I'm Hiring)
        role_map = {"Requests to me": "Hiring", "Requests I sent": "Doing"}
        items = [r for r in gigs if r["status"] == "Pending"
                 and (chosen is None or r["role"] == role_map[chosen])]
        items.sort(key=lambda r: r["start"], reverse=not st.session_state.asc_pending)

        with st.container(height=LIST_H, border=False):
            if items:
                render_cards(items, "pending")
            else:
                st.caption("No pending requests.")

    # ----- Completed: list only -----
    with tab_done:
        filt_col, sort_col = st.columns([4.726, 1.274], vertical_alignment="center")
        with filt_col:
            chosen = st.pills(
                "Filter", ["Sessions I did", "Sessions I offered"], selection_mode="single",
                label_visibility="collapsed", key="pills_done",
            )
        with sort_col:
            sort_button("done", "↑ Oldest first", "↓ Newest first")

        role_map = {"Sessions I did": "Doing", "Sessions I offered": "Hiring"}
        items = [r for r in gigs if r["status"] == "Completed"
                 and (chosen is None or r["role"] == role_map[chosen])]
        items.sort(key=lambda r: r["end"], reverse=not st.session_state.asc_done)

        with st.container(height=LIST_H, border=False):
            if items:
                render_cards(items, "done")
            else:
                st.caption("No completed gigs.")

    # ----- Cancelled: list only -----
    with tab_cancel:
        filt_col, sort_col = st.columns([4.726, 1.274], vertical_alignment="center")
        with filt_col:
            chosen = st.pills(
                "Filter", ["Cancelled by me", "Cancelled by others"], selection_mode="single",
                label_visibility="collapsed", key="pills_cancel",
            )
        with sort_col:
            sort_button("cancel", "↑ Oldest first", "↓ Newest first")

        who_map = {"Cancelled by me": "me", "Cancelled by others": "them"}
        items = [r for r in gigs if r["status"] == "Cancelled"
                 and (chosen is None or r["cancelled_by"] == who_map[chosen])]
        items.sort(key=lambda r: r["start"], reverse=not st.session_state.asc_cancel)

        with st.container(height=LIST_H, border=False):
            if items:
                render_cards(items, "cancel")
            else:
                st.caption("No cancelled gigs.")

# ---------- Right: gig details (replaces the to-do list) or to-do summary ----------
with right_col:
    selected = gigs_by_id.get(st.session_state.selected_gig)

    if selected is not None:
        st.subheader("Gig Details")
        st.caption("Press Back to return to your to-do list.")
        with st.container(height=TODO_H, border=False):
            # the "sort_" key prefix reuses the pill-button style
            st.button("← Back to To-Do", key="sort_back", on_click=close_gig)
            st.markdown(detail_html(selected), unsafe_allow_html=True)
            render_actions(selected)
    else:
        st.subheader("To-Do")
        todos = build_todos()
        overdue = sum(1 for t in todos if t[0] < today)
        st.caption(
            f"{len(todos)} open task(s)" + (f" · {overdue} overdue" if overdue else "")
        )

        with st.container(height=TODO_H, border=False):
            if todos:
                render_todos(todos)
            else:
                st.caption("You're all caught up.")