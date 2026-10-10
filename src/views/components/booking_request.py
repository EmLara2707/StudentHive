"""Booking Request page: opened by 'Request Booking' / 'Request Project' on a listing.

Three layouts, chosen from the listing (BookingKind):
  * Rental                  -> dates + times + pickup/return location (always shown)
  * Gig, Service deliverable -> dates + times + meeting mode (location only for On-Campus)
  * Gig, Project deliverable -> project details + deadline ("Project Request")

Layout only. Pricing, validation and sending live in BookingController. Styles:
views/styles/booking_request.css (uses .sh-badge / .sh-avatar / .sh-image from
marketplace.css, --ink / --muted from base.css).
"""
from datetime import datetime, time, timedelta
from html import escape

import streamlit as st

from controllers.booking_controller import COMING_SOON_MESSAGE, OWN_LISTING_ERROR
from models.booking_request import (
    BookingContext, BookingForm, BookingKind, MeetingMode, PriceQuote,
)
from repositories.errors import RepositoryError
from utils.clock import today_manila
from views.components.listing_components import render_listing_image
from views.components.repo_errors import loading, show_error
from views.components.styles import load_css
from views.session import get_booking_controller, get_current_email

# Time choices every 30 minutes, shown with AM/PM ("12:00 AM" ... "11:30 PM")
TIME_OPTIONS = [datetime(2000, 1, 1, h, m).strftime("%I:%M %p")
                for h in range(24) for m in (0, 30)]
DEFAULT_TIME = "10:00 AM"

_MODE_SUBTITLES = {
    MeetingMode.ONLINE: "Google Meet / Zoom / Teams link will be given",
    MeetingMode.CAMPUS: "Library, Cafeteria, etc.",
}


# ==========================================
# HELPERS
# ==========================================

def _to_time(label: str) -> time:
    """'10:00 AM' -> datetime.time(10, 0)"""
    return datetime.strptime(label, "%I:%M %p").time()


def _close() -> None:
    """Leave the request page (back to the listing detail)."""
    st.session_state.booking_listing_id = None
    st.session_state.pop("bk_mode", None)


def _set_mode(value: MeetingMode) -> None:
    st.session_state.bk_mode = value


def _money(v: float) -> str:
    return f"₱{v:,.0f}" if float(v).is_integer() else f"₱{v:,.2f}"


def _mode_card(mode: MeetingMode, selected: bool) -> None:
    """Big selectable card (HTML look + invisible button on top)."""
    key = "online" if mode is MeetingMode.ONLINE else "campus"
    with st.container(key=f"mode_{key}"):
        st.markdown(
            f"<div class='sh-mode{' selected' if selected else ''}'>"
            f"<div class='ttl'>{escape(mode.value)}</div>"
            f"<div class='sub'>{escape(_MODE_SUBTITLES[mode])}</div></div>",
            unsafe_allow_html=True,
        )
        st.button(f"Select {mode.value}", key=f"modepick_{key}", on_click=_set_mode, args=(mode,))


def _notice(unit: str) -> str:
    if unit == "day":
        return "This item is listed with fixed daily rates. Hourly booking is not available for this listing."
    if unit == "hr":
        return "This item is listed with fixed hourly rates. Daily booking is not available for this listing."
    return "This item is listed with a one-time payment. The total stays the same for any dates you choose."


def _rating_line(context: BookingContext) -> str:
    r = context.owner_rating
    if r.count == 0:
        return "No reviews yet"
    noun = "review" if r.count == 1 else "reviews"
    return f"<b>★</b> {r.average:.1f} ({r.count} {noun})"


def _summary_html(context: BookingContext, quote: PriceQuote) -> str:
    """Price summary box for the right-hand card."""
    listing = context.listing
    unit = listing.unit
    is_rental = context.kind is BookingKind.RENTAL
    rate_lbl = "Rental Rate" if is_rental else "Base Rate"
    if context.kind is BookingKind.PROJECT or unit == "once":
        rows = [("Base Price", _money(listing.price))]
    else:
        qty = quote.quantity
        per = "day" if unit == "day" else "hour"
        word = ("day" if qty == 1 else "days") if unit == "day" else ("hour" if qty == 1 else "hours")
        num = "Num of Days" if unit == "day" else "Num of Hours"
        if qty is not None:
            num = f"{qty:g} {word}"
        rows = [
            (rate_lbl, f"{_money(listing.price)} / {per}"),
            (f"Subtotal ({num} x {rate_lbl})",
             _money(quote.subtotal) if quote.subtotal is not None else "—"),
        ]

    rows_html = "".join(
        f"<div class='sh-bk-row'><span>{escape(a)}</span><span>{escape(b)}</span></div>"
        for a, b in rows
    )
    kind = listing.deliverable_kind
    badges = (
        f"<span class='sh-badge sh-badge-{escape(listing.category.lower())}'>"
        f"{'Gigs' if listing.is_gig else 'Rental'}</span>"
        + (f"<span class='sh-badge sh-badge-kind'>{escape(kind)}</span>" if kind else "")
    )
    owner_name = context.owner_name
    return (
        f"<div class='sh-bk-body'>"
        f"<div class='sh-bk-badges'>{badges}</div>"
        f"<div class='sh-bk-name'>{escape(listing.title)}</div>"
        f"<div class='sh-bk-owner'><div class='sh-avatar'>{escape(owner_name[:1].upper())}</div>"
        f"<div><div class='nm'>{escape(owner_name)}</div>"
        f"<div class='rt'>{_rating_line(context)}</div></div></div>"
        f"<hr class='sh-bk-hr'><div class='sh-bk-ps'>Price Summary</div>{rows_html}"
        f"<hr class='sh-bk-hr'>"
        f"<div class='sh-bk-total'><span class='lbl'>Total</span>"
        f"<span class='amt'>{_money(quote.subtotal) if quote.subtotal is not None else chr(8212)}</span></div></div>"
    )


# ==========================================
# PAGE
# ==========================================

def render_booking_request(listing_id: int) -> None:
    """Draw the whole Booking Request / Project Request page."""
    booking = get_booking_controller()
    email = get_current_email()
    with loading("Loading listing...", "Couldn't load this listing.", key="retry_booking"):
        context = booking.get_context(listing_id)
    if context is None or not booking.can_book(context.listing, email):
        # gone/closed, or the user's own listing: send them back to the Marketplace
        if context is not None:
            st.toast(OWN_LISTING_ERROR)
        _close()
        st.rerun()
        return
    listing = context.listing

    load_css("booking_request")
    st.session_state.setdefault("bk_mode", MeetingMode.ONLINE)

    is_rental = context.kind is BookingKind.RENTAL
    is_project = context.kind is BookingKind.PROJECT
    unit = listing.unit
    cta = "Request Project" if is_project else "Request Booking"
    form_cta = (None if is_project else
                {"day": "Request for Hourly Rates", "hr": "Request for Daily Rates"}.get(unit, "Request Booking"))
    lid = listing.id
    # Rentals use pickup/return wording; Gig (Service) uses its own wording
    start_lbl = "Start / Pickup Date" if is_rental else "Start Date"
    end_lbl = "End / Return Date" if is_rental else "End Date"
    loc_lbl = "Proposed Pickup / Return Location" if is_rental else "Location Meet-up"

    st.button("Back to Listing", key="back_btn", on_click=_close)
    st.markdown(
        f"<div class='sh-bk-title'>{'Project Request' if is_project else 'Booking Request'}</div>",
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.65, 1], gap="large")

    # ---------------- left: the request form ----------------
    form = BookingForm()

    with left:
        with st.container(key="book_form"):
            if is_project:
                st.markdown("<div class='sh-bk-h'>Project Details</div>", unsafe_allow_html=True)
                form.details = st.text_area("Project details", height=170, key=f"bk_details_{lid}",
                                            label_visibility="collapsed")
                st.markdown("<div class='sh-bk-h'>Deadline and Timeline</div>", unsafe_allow_html=True)
                form.deadline = st.date_input("Deadline", value=today_manila() + timedelta(days=7),
                                              min_value=today_manila(), format="MM/DD/YYYY",
                                              key=f"bk_deadline_{lid}", label_visibility="collapsed")
            else:
                st.markdown(f"<div class='sh-bk-notice'>{escape(_notice(unit))}</div>",
                            unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    form.start_date = st.date_input(start_lbl, value=today_manila(),
                                                    min_value=today_manila(), format="MM/DD/YYYY",
                                                    key=f"bk_start_{lid}")
                    form.start_time = _to_time(st.selectbox(
                        "Start time", TIME_OPTIONS, index=TIME_OPTIONS.index(DEFAULT_TIME),
                        key=f"bk_start_t_{lid}", label_visibility="collapsed"))
                with c2:
                    if unit == "hr":
                        # hourly rates: the end date always follows the start date and is locked
                        st.session_state[f"bk_end_{lid}"] = form.start_date
                        form.end_date = st.date_input(end_lbl, format="MM/DD/YYYY",
                                                      key=f"bk_end_{lid}", disabled=True)
                    else:
                        default_end = today_manila() + timedelta(days=1 if unit == "day" else 0)
                        form.end_date = st.date_input(end_lbl, value=default_end,
                                                      format="MM/DD/YYYY", key=f"bk_end_{lid}")
                    form.end_time = _to_time(st.selectbox(
                        "End time", TIME_OPTIONS, index=TIME_OPTIONS.index(DEFAULT_TIME),
                        key=f"bk_end_t_{lid}", label_visibility="collapsed"))

                needs_location = is_rental
                if not is_rental:
                    form.meeting_mode = st.session_state.bk_mode
                    st.markdown("<div class='sh-bk-lbl'>Meeting Mode</div>", unsafe_allow_html=True)
                    m1, m2 = st.columns(2)
                    with m1:
                        _mode_card(MeetingMode.ONLINE, form.meeting_mode is MeetingMode.ONLINE)
                    with m2:
                        _mode_card(MeetingMode.CAMPUS, form.meeting_mode is MeetingMode.CAMPUS)
                    needs_location = form.meeting_mode is MeetingMode.CAMPUS

                if needs_location:
                    form.location = st.text_area(loc_lbl, height=110, key=f"bk_loc_{lid}")

            submit_main = (st.button(form_cta, key="book_submit_main", width="stretch")
                           if form_cta else False)
            st.markdown(
                "<div class='sh-bk-fine'>Kindly review the details as it can no longer be "
                "edited as soon as you confirm.</div>",
                unsafe_allow_html=True,
            )

    # ---------------- price ----------------
    quote = booking.quote(context, form)

    # ---------------- right: summary card ----------------
    with right:
        with st.container(key="book_summary"):
            render_listing_image(listing, height=130, badge=False)
            st.markdown(_summary_html(context, quote), unsafe_allow_html=True)
            with st.container(key="book_summary_btn"):
                submit_side = st.button(cta, key="book_submit_side", width="stretch")
        st.markdown(
            "<div class='sh-bk-note'>Kindly communicate with the provider regarding their "
            "payment methods and their contact info can be found in their profile.</div>",
            unsafe_allow_html=True,
        )

    # ---------------- submit ----------------
    if submit_main and not booking.rate_request_available(context):
        st.toast(COMING_SOON_MESSAGE)
    elif submit_main or submit_side:
        try:
            with st.spinner("Sending your request..."):
                result = booking.submit(listing.id, email, form)
        except RepositoryError as exc:       # nothing was sent: the form stays filled in
            with left:
                show_error(exc, "Couldn't send your request.")
            return
        if not result.ok:
            with left:
                for message in result.errors:
                    st.error(message)
        else:
            _close()
            st.session_state.selected_listing_id = None   # back to the Marketplace grid
            st.toast("Your request has been sent!")
            st.rerun()