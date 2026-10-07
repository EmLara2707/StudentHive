"""Dashboard page: welcome header, My Listings, mini calendar + schedule dialog.
Layout only. Which listings/events to show lives in DashboardController."""
import calendar
from datetime import date
from html import escape

import streamlit as st

from models.event import CalendarEvent, EventKind
from utils.dates import first_of_month, shift_month
from views.components.styles import load_css
from views.session import get_dashboard_controller

# NOTE: do NOT call st.set_page_config here. App.py already does it.

GIG_COLOR = "#0F9D8A"
RENTAL_COLOR = "#F5A03C"
PLACEHOLDER_IMAGE = "https://placehold.co/200"
WEEKDAYS_LONG = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
WEEKDAYS_SHORT = ["S", "M", "T", "W", "T", "F", "S"]

load_css("dashboard")


# ------------------------------------------------------------ data access
def _email() -> str:
    return (st.session_state.get("user") or {}).get("email", "")


def _events() -> list[CalendarEvent]:
    return get_dashboard_controller().get_events(_email())


# ------------------------------------------------------------ html builders
def _badge_class(kind: str) -> str:
    return "badge-gig" if kind == EventKind.GIG.value else "badge-rental"


def listing_card(listing) -> str:
    """One listing card as a single-line HTML string.

    No indentation or blank lines on purpose: Markdown treats lines
    indented 4+ spaces as a code block and would print the raw HTML.
    """
    image = listing.images[0] if listing.images else PLACEHOLDER_IMAGE
    return (
        '<div class="listing-card">'
        f'<img src="{escape(image)}">'
        '<div class="listing-info">'
        f'<div class="listing-name">{escape(listing.title)}</div>'
        '<div class="listing-meta">'
        f'<span class="badge {_badge_class(listing.category)}">{escape(listing.category)}</span>'
        f'<span class="listing-price">{escape(listing.price_label)}</span>'
        '</div>'
        '</div>'
        '</div>'
    )


def event_row(e: CalendarEvent) -> str:
    return (
        '<div class="ev-row">'
        '<div class="ev-date">'
        f'<div class="ev-mon">{e.date:%b}</div>'
        f'<div class="ev-day">{e.date.day}</div>'
        '</div>'
        '<div class="ev-info">'
        f'<div class="ev-title">{escape(e.title)}</div>'
        f'<div class="ev-sub">{escape(e.time)} · {escape(e.price_label)}</div>'
        '</div>'
        f'<span class="badge {_badge_class(e.kind.value)}">{escape(e.kind.value)}</span>'
        '</div>'
    )


def marker_css(view: date, events_by_day: dict, today: date) -> str:
    """Dots under days that have events, plus a highlight for today.
    Stays in Python because the selectors depend on the data."""
    rules = []
    base = (
        "content:'';position:absolute;bottom:5px;left:50%;"
        "width:6px;height:6px;border-radius:50%;"
    )
    ctrl = get_dashboard_controller()
    for d, evs in events_by_day.items():
        if (d.year, d.month) != (view.year, view.month):
            continue
        kinds = ctrl.kinds(evs)
        sel = f".st-key-cal_box .st-key-day_{d:%Y%m%d} button::after"
        if len(kinds) > 1:  # gig + rental on the same day: two dots
            rules.append(
                f"{sel}{{{base}background:{GIG_COLOR};"
                f"box-shadow:10px 0 0 {RENTAL_COLOR};transform:translateX(-8px);}}"
            )
        else:
            color = GIG_COLOR if EventKind.GIG in kinds else RENTAL_COLOR
            rules.append(f"{sel}{{{base}background:{color};transform:translateX(-3px);}}")

    if (today.year, today.month) == (view.year, view.month):
        rules.append(
            f".st-key-cal_box .st-key-day_{today:%Y%m%d} button{{background:#CDEEE9;}}"
        )
    return "<style>" + "".join(rules) + "</style>" if rules else ""


# ------------------------------------------------------------ callbacks
def _shift(key: str, delta: int) -> None:
    st.session_state[key] = shift_month(st.session_state[key], delta)


def _dialog_go_today() -> None:
    st.session_state.dlg_month = first_of_month(date.today())
    st.session_state.dlg_selected = date.today()


# ------------------------------------------------------------ dialog
@st.dialog("Schedule", width="large")
def calendar_dialog() -> None:
    ctrl = get_dashboard_controller()
    events = _events()
    by_day = ctrl.group_by_day(events)
    today = date.today()
    view = st.session_state.dlg_month
    selected = st.session_state.dlg_selected

    prev_col, title_col, next_col, today_col = st.columns([1, 4, 1, 2], vertical_alignment="center")
    prev_col.button("‹", key="dlg_prev", on_click=_shift, args=("dlg_month", -1), use_container_width=True)
    title_col.markdown(f'<div class="dlg-title">{view:%B %Y}</div>', unsafe_allow_html=True)
    next_col.button("›", key="dlg_next", on_click=_shift, args=("dlg_month", 1), use_container_width=True)
    today_col.button("Today", key="dlg_today", on_click=_dialog_go_today, use_container_width=True)

    # Month grid with event chips
    html = '<div class="dgrid">'
    html += "".join(f'<div class="dhead">{n}</div>' for n in WEEKDAYS_LONG)
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
            day_events = by_day.get(d, [])
            chips = "".join(
                f'<div class="chip chip-{e.kind.value.lower()}">{escape(e.title)}</div>'
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
        selected_events = by_day.get(selected, [])
        if selected_events:
            st.markdown("".join(event_row(e) for e in selected_events), unsafe_allow_html=True)
        else:
            st.caption("Nothing scheduled.")
    with right:
        st.markdown(f"**{view:%B %Y} agenda**")
        month_events = ctrl.in_month(events, view.year, view.month)
        if month_events:
            st.markdown("".join(event_row(e) for e in month_events), unsafe_allow_html=True)
        else:
            st.caption("No gigs or rentals this month.")


# ------------------------------------------------------------ page
ctrl = get_dashboard_controller()
today = date.today()
events = _events()
events_by_day = ctrl.group_by_day(events)

if "cal_month" not in st.session_state:
    st.session_state.cal_month = first_of_month(today)

name = (st.session_state.get("user") or {}).get("name", "User")

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

    listings = ctrl.get_listings(_email())
    with st.container(key="list_box"):
        if listings:
            cards_html = "".join(listing_card(l) for l in listings)
            st.markdown(f'<div class="listing-grid">{cards_html}</div>', unsafe_allow_html=True)
        else:
            st.caption("You haven't posted any listings yet.")

# ---------- Right: calendar ----------
with right_col:
    st.subheader("Calendar")

    view = st.session_state.cal_month
    clicked = None

    with st.container(border=False, key="cal_box"):
        prev_col, title_col, next_col = st.columns([1, 4, 1], vertical_alignment="center")
        prev_col.button("‹", key="cal_prev", on_click=_shift, args=("cal_month", -1), use_container_width=True)
        title_col.markdown(f'<div class="cal-title">{view:%B %Y}</div>', unsafe_allow_html=True)
        next_col.button("›", key="cal_next", on_click=_shift, args=("cal_month", 1), use_container_width=True)

        # Weekday labels (+ the dot styles for this month's events)
        week_header = (
            '<div class="cal-week">'
            + "".join(f"<div>{w}</div>" for w in WEEKDAYS_SHORT)
            + "</div>"
        )
        st.markdown(week_header + marker_css(view, events_by_day, today), unsafe_allow_html=True)

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
        upcoming = ctrl.upcoming(events, today)
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
        st.session_state.dlg_month = first_of_month(clicked)
        st.session_state.dlg_selected = clicked
        calendar_dialog()
