"""Booking Request page: opened by 'Request Booking' / 'Request Project' on a listing.

Three layouts, chosen from the listing:
  * Rental                  -> dates + times + pickup/return location (always shown)
  * Gig, Service deliverable -> dates + times + meeting mode (location only for On-Campus)
  * Gig, Project deliverable -> project details + deadline ("Project Request")

Colors and fonts (--teal-hover, --ink, --muted, Montserrat, Inter) come from the
style block at the top of Marketplace.py.
"""
from datetime import date, datetime, time, timedelta
from html import escape

import streamlit as st

from views.components.listing_components import render_listing_image

# ==========================================
# STYLES (Booking Request page only)
# ==========================================

BOOKING_CSS = """
:root {
    --bk-line: #c5ced6;
    --bk-teal: #0b9488;
    --bk-soft: #e8edf1;
}

.sh-bk-title {
    font-family: 'Montserrat', sans-serif;
    font-weight: 800;
    font-size: 2.4rem;
    line-height: 1.2;
    color: var(--ink);
    margin: 0.4rem 0 1rem;
}

/* ---------- form card (left) ---------- */
.st-key-book_form {
    border: 1px solid var(--bk-line);
    border-radius: 34px;
    padding: 1.8rem 1.8rem 1.4rem !important;
    gap: 0.7rem;
}
/* Streamlit gives markdown a -1rem bottom margin; remove it */
.st-key-book_form [data-testid="stMarkdownContainer"],
.st-key-book_summary [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }

.sh-bk-notice {
    background: var(--bk-soft);
    border-radius: 20px;
    padding: 0.9rem 1.4rem;
    text-align: center;
    font-family: 'Inter', sans-serif;
    font-size: 0.95rem;
    line-height: 1.35;
    color: var(--ink);
}
.sh-bk-lbl { font-size: 0.85rem; color: var(--muted); margin-top: 0.3rem; }
.sh-bk-h {
    font-family: 'Montserrat', sans-serif;
    font-weight: 700;
    font-size: 1.1rem;
    color: #4b5560;
    margin-top: 0.2rem;
}
.sh-bk-fine {
    text-align: center;
    font-size: 0.72rem;
    color: var(--muted);
}

.st-key-book_form [data-testid="stWidgetLabel"] p {
    font-size: 0.85rem;
    color: var(--muted);
    margin-bottom: 0;
}
/* pill-shaped date + time fields */
.st-key-book_form [data-testid="stDateInput"] [data-baseweb="input"],
.st-key-book_form [data-testid="stSelectbox"] [data-baseweb="select"] > div {
    border: 1px solid var(--bk-line) !important;
    border-radius: 999px !important;
    background: #ffffff !important;
}
.st-key-book_form [data-testid="stDateInput"] input,
.st-key-book_form [data-testid="stSelectbox"] input {
    text-align: center;
}
.st-key-book_form [data-testid="stSelectbox"] [data-baseweb="select"] > div {
    justify-content: center;
}
/* rounded text areas */
.st-key-book_form [data-testid="stTextAreaRootElement"],
.st-key-book_form [data-testid="stTextArea"] [data-baseweb="textarea"] {
    border: 1px solid var(--bk-line) !important;
    border-radius: 22px !important;
    background: #ffffff !important;
}
/* teal focus instead of Streamlit's default red */
.st-key-book_form [data-testid="stTextAreaRootElement"]:focus-within,
.st-key-book_form [data-testid="stDateInput"] [data-baseweb="input"]:focus-within {
    border-color: var(--bk-teal) !important;
    box-shadow: 0 0 0 1px var(--bk-teal) !important;
}

/* ---------- meeting mode cards (invisible button stretched over the card) ---------- */
[class*="st-key-mode_"] { position: relative; gap: 0; }
[class*="st-key-mode_"] [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }
[class*="st-key-modepick_"] {
    position: absolute !important;
    top: 0; left: 0; right: 0; bottom: 0;
    width: 100% !important;
    height: 100% !important;
    margin: 0 !important;
    z-index: 5;
}
[class*="st-key-modepick_"] [data-testid="stButton"],
[class*="st-key-modepick_"] button {
    position: static;
    width: 100% !important;
    height: 100% !important;
    min-height: 0;
    opacity: 0;
    cursor: pointer;
}
.sh-mode {
    border: 1px solid var(--bk-line);
    border-radius: 20px;
    padding: 1rem 1.1rem;
    background: #ffffff;
    text-align: left;
    min-height: 5.6rem;
    transition: border-color 0.15s;
}
.sh-mode .ttl {
    font-family: 'Montserrat', sans-serif;
    font-weight: 700;
    font-size: 1.35rem;
    line-height: 1.2;
    color: var(--ink);
}
.sh-mode .sub {
    font-family: 'Inter', sans-serif;
    font-size: 0.72rem;
    color: #4b5560;
    margin-top: 0.3rem;
}
[class*="st-key-mode_"]:hover .sh-mode { border-color: var(--bk-teal); }
.sh-mode.selected { background: var(--bk-teal); border-color: var(--bk-teal); }
.sh-mode.selected .ttl, .sh-mode.selected .sub { color: #ffffff; }

/* ---------- submit buttons ---------- */
[class*="st-key-book_submit"] button {
    background: var(--bk-teal);
    border: none;
    border-radius: 10px;
    min-height: 2.2rem;
}
[class*="st-key-book_submit"] button p {
    color: #ffffff;
    font-weight: 700;
    font-size: 0.85rem;
}
[class*="st-key-book_submit"] button:hover,
[class*="st-key-book_submit"] button:focus:not(:active) {
    background: var(--teal-hover, #0b5750);
    border: none;
    color: #ffffff;
}

/* ---------- summary card (right) ---------- */
.st-key-book_summary {
    border: 1px solid var(--bk-line);
    border-radius: 34px;
    overflow: hidden;
    padding: 0 !important;
    gap: 0;
}
.st-key-book_summary .sh-image { border-radius: 0; }
.st-key-book_summary_btn { padding: 0 1.1rem 1.1rem !important; }

.sh-bk-body { padding: 0.9rem 1.1rem 0.4rem; }
.sh-bk-badges { display: flex; gap: 6px; margin-bottom: 0.5rem; }
.sh-bk-name {
    font-family: 'Montserrat', sans-serif;
    font-weight: 800;
    font-size: 1.5rem;
    line-height: 1.2;
    color: var(--ink);
}
.sh-bk-owner { display: flex; align-items: center; gap: 0.6rem; margin: 0.6rem 0; }
.sh-bk-owner .nm { font-weight: 700; font-size: 0.8rem; color: var(--ink); line-height: 1.2; }
.sh-bk-owner .rt { font-size: 0.65rem; color: var(--muted); }
.sh-bk-owner .rt b { color: #f5b23c; }
.sh-bk-hr { border: none; border-top: 1px solid #8a939b; margin: 0.5rem 0; }
.sh-bk-ps { font-weight: 700; font-size: 0.75rem; color: var(--ink); }
.sh-bk-row {
    display: flex;
    justify-content: space-between;
    gap: 0.8rem;
    font-size: 0.72rem;
    color: var(--muted);
    margin: 0.35rem 0;
}
.sh-bk-row span:last-child { white-space: nowrap; }
.sh-bk-total {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: 'Montserrat', sans-serif;
    font-weight: 800;
    margin-bottom: 0.4rem;
}
.sh-bk-total .lbl { font-size: 1.15rem; color: var(--ink); }
.sh-bk-total .amt { font-size: 1.5rem; color: var(--bk-teal); }
.sh-bk-note { font-size: 0.7rem; color: var(--muted); margin: 0.7rem 0.4rem 0; }
"""

# ==========================================
# HELPERS
# ==========================================

ONLINE, CAMPUS = "Online Meeting", "On-Campus"

# Time choices every 30 minutes, shown with AM/PM ("12:00 AM" ... "11:30 PM")
TIME_OPTIONS = [datetime(2000, 1, 1, h, m).strftime("%I:%M %p")
                for h in range(24) for m in (0, 30)]
DEFAULT_TIME = "10:00 AM"


def _to_time(label: str) -> time:
    """'10:00 AM' -> datetime.time(10, 0)"""
    return datetime.strptime(label, "%I:%M %p").time()


def _back() -> None:
    """Return to the listing detail page."""
    st.session_state.booking_listing_id = None
    st.session_state.pop("bk_mode", None)


def _set_mode(value: str) -> None:
    st.session_state.bk_mode = value


def _money(v: float) -> str:
    return f"\u20b1{v:,.0f}" if float(v).is_integer() else f"\u20b1{v:,.2f}"


def _calc(unit: str, price: float, start: datetime, end: datetime):
    """Returns (quantity, subtotal, error). Quantity is days, hours or 1 (one-time)."""
    if unit == "day":
        if end.date() < start.date():
            return None, None, "The return date must be on or after the pickup date."
        qty = max((end.date() - start.date()).days, 1)
    elif unit == "hr":
        secs = (end - start).total_seconds()
        if secs <= 0:
            return None, None, "The end date and time must be after the start."
        qty = round(secs / 3600, 2)
    else:
        qty = 1
    return qty, price * qty, None


def _mode_card(key: str, title: str, sub: str, selected: bool) -> None:
    """Big selectable card (HTML look + invisible button on top)."""
    with st.container(key=f"mode_{key}"):
        st.markdown(
            f"<div class='sh-mode{' selected' if selected else ''}'>"
            f"<div class='ttl'>{escape(title)}</div>"
            f"<div class='sub'>{escape(sub)}</div></div>",
            unsafe_allow_html=True,
        )
        st.button(f"Select {title}", key=f"modepick_{key}", on_click=_set_mode, args=(title,))


def _notice(unit: str) -> str:
    if unit == "day":
        return "This item is listed with fixed daily rates. Hourly booking is not available for this listing."
    if unit == "hr":
        return "This item is listed with fixed hourly rates. Daily booking is not available for this listing."
    return "This item is listed with a one-time payment. The total stays the same for any dates you choose."


def _summary_html(listing, owner_name: str, is_rental: bool, is_project: bool, qty, subtotal) -> str:
    """Price summary box for the right-hand card."""
    unit = listing.unit
    rate_lbl = "Rental Rate" if is_rental else "Base Rate"
    if is_project or unit == "once":
        rows = [("Base Price", _money(listing.price))]
        total = listing.price
    else:
        per = "day" if unit == "day" else "hour"
        word = ("day" if qty == 1 else "days") if unit == "day" else ("hour" if qty == 1 else "hours")
        num = "Num of Days" if unit == "day" else "Num of Hours"
        if qty is not None:
            num = f"{qty:g} {word}"
        rows = [
            (rate_lbl, f"{_money(listing.price)} / {per}"),
            (f"Subtotal ({num} x {rate_lbl})", _money(subtotal) if subtotal is not None else "\u2014"),
        ]
        total = subtotal

    rows_html = "".join(
        f"<div class='sh-bk-row'><span>{escape(a)}</span><span>{escape(b)}</span></div>"
        for a, b in rows
    )
    kind = listing.deliverable_kind
    badges = (
        f"<span class='sh-badge sh-badge-{escape(listing.category.lower())}'>"
        f"{'Gigs' if listing.category == 'Gig' else 'Rental'}</span>"
        + (f"<span class='sh-badge sh-badge-kind'>{escape(kind)}</span>" if kind else "")
    )
    # NOTE: rating is placeholder text from the design (the Listing model has no ratings yet)
    return (
        f"<div class='sh-bk-body'>"
        f"<div class='sh-bk-badges'>{badges}</div>"
        f"<div class='sh-bk-name'>{escape(listing.title)}</div>"
        f"<div class='sh-bk-owner'><div class='sh-avatar'>{escape(owner_name[:1].upper())}</div>"
        f"<div><div class='nm'>{escape(owner_name)}</div>"
        f"<div class='rt'><b>\u2605</b> 4.8 (124 reviews)</div></div></div>"
        f"<hr class='sh-bk-hr'><div class='sh-bk-ps'>Price Summary</div>{rows_html}"
        f"<hr class='sh-bk-hr'>"
        f"<div class='sh-bk-total'><span class='lbl'>Total</span>"
        f"<span class='amt'>{_money(total) if total is not None else chr(8212)}</span></div></div>"
    )


# ==========================================
# PAGE
# ==========================================

def render_booking_request(market, listing_id: int) -> None:
    """Draw the whole Booking Request / Project Request page."""
    entry = market.get_entry(listing_id)
    if entry is None:
        st.session_state.booking_listing_id = None
        st.rerun()
        return
    listing = entry.listing

    st.markdown(f"<style>{BOOKING_CSS}</style>", unsafe_allow_html=True)
    st.session_state.setdefault("bk_mode", ONLINE)

    is_rental = listing.category == "Rental"
    is_project = listing.deliverable_kind == "Project"
    unit = listing.unit
    cta = "Request Project" if is_project else "Request Booking"
    form_cta = ("Send Project Request" if is_project else
                {"day": "Request for Daily Rates", "hr": "Request for Hourly Rates"}.get(unit, "Request Booking"))
    lid = listing.id
    # Rentals use pickup/return wording; Gig (Service) uses its own wording
    start_lbl = "Start / Pickup Date" if is_rental else "Start Date"
    end_lbl = "End / Return Date" if is_rental else "End Date"
    loc_lbl = "Proposed Pickup / Return Location" if is_rental else "Location Meet-up"

    st.button("Back to Listing", key="back_btn", on_click=_back)
    st.markdown(
        f"<div class='sh-bk-title'>{'Project Request' if is_project else 'Booking Request'}</div>",
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.65, 1], gap="large")

    # ---------------- left: the request form ----------------
    details = location = ""
    start_d = end_d = deadline = None
    start_t = end_t = time(10, 0)
    mode = None

    with left:
        with st.container(key="book_form"):
            if is_project:
                st.markdown("<div class='sh-bk-h'>Project Details</div>", unsafe_allow_html=True)
                details = st.text_area("Project details", height=170, key=f"bk_details_{lid}",
                                       label_visibility="collapsed")
                st.markdown("<div class='sh-bk-h'>Deadline and Timeline</div>", unsafe_allow_html=True)
                deadline = st.date_input("Deadline", value=date.today() + timedelta(days=7),
                                         min_value=date.today(), format="MM/DD/YYYY",
                                         key=f"bk_deadline_{lid}", label_visibility="collapsed")
            else:
                st.markdown(f"<div class='sh-bk-notice'>{escape(_notice(unit))}</div>",
                            unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    start_d = st.date_input(start_lbl, value=date.today(),
                                            min_value=date.today(), format="MM/DD/YYYY",
                                            key=f"bk_start_{lid}")
                    start_t = _to_time(st.selectbox(
                        "Start time", TIME_OPTIONS, index=TIME_OPTIONS.index(DEFAULT_TIME),
                        key=f"bk_start_t_{lid}", label_visibility="collapsed"))
                with c2:
                    if unit == "hr":
                        # hourly rates: the end date always follows the start date and is locked
                        st.session_state[f"bk_end_{lid}"] = start_d
                        end_d = st.date_input(end_lbl, format="MM/DD/YYYY",
                                              key=f"bk_end_{lid}", disabled=True)
                    else:
                        default_end = date.today() + timedelta(days=1 if unit == "day" else 0)
                        end_d = st.date_input(end_lbl, value=default_end,
                                              format="MM/DD/YYYY", key=f"bk_end_{lid}")
                    end_t = _to_time(st.selectbox(
                        "End time", TIME_OPTIONS, index=TIME_OPTIONS.index(DEFAULT_TIME),
                        key=f"bk_end_t_{lid}", label_visibility="collapsed"))

                needs_location = is_rental
                if not is_rental:
                    mode = st.session_state.bk_mode
                    st.markdown("<div class='sh-bk-lbl'>Meeting Mode</div>", unsafe_allow_html=True)
                    m1, m2 = st.columns(2)
                    with m1:
                        _mode_card("online", ONLINE, "Google Meet / Zoom / Teams link will be given",
                                   mode == ONLINE)
                    with m2:
                        _mode_card("campus", CAMPUS, "Library, Cafeteria, etc.", mode == CAMPUS)
                    needs_location = mode == CAMPUS

                if needs_location:
                    location = st.text_area(loc_lbl, height=110,
                                            key=f"bk_loc_{lid}")

            submit_main = st.button(form_cta, key="book_submit_main", width="stretch")
            st.markdown(
                "<div class='sh-bk-fine'>Kindly review the details as it can no longer be "
                "edited as soon as you confirm.</div>",
                unsafe_allow_html=True,
            )

    # ---------------- price ----------------
    qty = subtotal = err = None
    if is_project:
        subtotal = listing.price
    else:
        qty, subtotal, err = _calc(unit, listing.price,
                                   datetime.combine(start_d, start_t),
                                   datetime.combine(end_d, end_t))

    # ---------------- right: summary card ----------------
    with right:
        with st.container(key="book_summary"):
            render_listing_image(listing, height=130, badge=False)
            st.markdown(_summary_html(listing, entry.owner.name, is_rental, is_project, qty, subtotal),
                        unsafe_allow_html=True)
            with st.container(key="book_summary_btn"):
                submit_side = st.button(cta, key="book_submit_side", width="stretch")
        st.markdown(
            "<div class='sh-bk-note'>Kindly communicate with the provider regarding their "
            "payment methods and their contact info can be found in their profile.</div>",
            unsafe_allow_html=True,
        )

    # ---------------- submit ----------------
    # "Request for Daily Rates" / "Request for Hourly Rates" are not available yet
    if submit_main and not is_project and unit in ("day", "hr"):
        st.toast("Coming soon!")
    elif submit_main or submit_side:
        problems = []
        if is_project:
            if not details.strip():
                problems.append("Please describe your project.")
            if deadline < date.today():
                problems.append("The deadline can't be in the past.")
        else:
            if err:
                problems.append(err)
            if (is_rental or mode == CAMPUS) and not location.strip():
                problems.append("Please enter a proposed pickup / return location." if is_rental
                                else "Please enter a meet-up location.")

        if problems:
            with left:
                for p in problems:
                    st.error(p)
        else:
            if is_project:
                info = {"project_details": details.strip(), "deadline": deadline.isoformat()}
                when = deadline.isoformat()
            else:
                info = {
                    "start": datetime.combine(start_d, start_t).isoformat(timespec="minutes"),
                    "end": datetime.combine(end_d, end_t).isoformat(timespec="minutes"),
                    "meeting_mode": mode,
                    "location": location.strip(),
                }
                when = start_d.isoformat()
            market.add_booking(listing_id=listing.id, date=when,
                               total=subtotal, details=info)
            st.session_state.booking_listing_id = None
            st.session_state.selected_listing_id = None   # back to the Marketplace grid
            st.session_state.pop("bk_mode", None)
            st.toast("Your request has been sent!")
            st.rerun()