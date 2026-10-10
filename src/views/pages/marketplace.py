"""Marketplace page: browse, listing detail, create-listing wizard, booking request.
Layout and navigation only; search/filter rules live in MarketplaceController.

Which sub-view shows is decided by session state that the sub-views and the
listing components set: the wizard draft (is_creating_listing), booking_listing_id
and selected_listing_id. Page styles: views/styles/marketplace.css."""
from enum import Enum, auto

import streamlit as st

from controllers.marketplace_controller import FILTER_OPTIONS, KIND_OPTIONS
from views.components.booking_request import render_booking_request
from views.components.listing_components import (
    render_listing_detail, render_listing_grid, render_side_panel,
)
from views.components.listing_wizard import render_create_listing
from views.components.repo_errors import loading
from views.components.styles import load_css
from views.components.user_profile import render_open_profile
from views.session import (
    get_marketplace_controller, is_creating_listing, start_listing_wizard,
)

# NOTE: do NOT call st.set_page_config here. App.py already does it.


class _View(Enum):
    CREATE = auto()
    BOOKING = auto()
    DETAIL = auto()
    BROWSE = auto()


def _current_view() -> _View:
    """Priority: wizard, then booking request, then listing detail, else the grid."""
    if is_creating_listing():
        return _View.CREATE
    if st.session_state.get("booking_listing_id") is not None:
        return _View.BOOKING
    if st.session_state.get("selected_listing_id") is not None:
        return _View.DETAIL
    return _View.BROWSE


# ------------------------------------------------------------ callbacks
def _open_listing(listing_id: int) -> None:
    st.session_state.selected_listing_id = listing_id


def _close_listing() -> None:
    st.session_state.selected_listing_id = None


def _open_create() -> None:
    """'Add a Listing' clicked: start a fresh wizard and show the Create page."""
    start_listing_wizard()


# ------------------------------------------------------------ browse
def _render_browse(market) -> None:
    # Everything above the grid is one keyed container that marketplace.css pins to the top.
    with st.container(key="market_header"):
        left, right = st.columns([3, 2], vertical_alignment="top")
        with left:
            st.title("Marketplace")
            st.caption("Browse verified Gigs and Rentals across your campus")
        with right:
            query = st.text_input("Search", placeholder="\U0001F50D  Search listings",
                                  label_visibility="collapsed", key="market_search")
            add_col, pills_col, kind_col = st.columns([1.2, 1.5, 1.6], vertical_alignment="center")
            with add_col:
                st.button("Add a Listing", icon=":material/add:", key="add_listing_btn",
                          on_click=_open_create)
            with pills_col:
                with st.container(key="filter_pills"):
                    # single select: one pill at a time, none selected = show everything
                    chosen = st.pills("Filter", FILTER_OPTIONS, selection_mode="single",
                                      label_visibility="collapsed", key="market_filter")

            kind_choice = None
            if market.shows_kind_filter(chosen):
                with kind_col:
                    with st.container(key="kind_pills"):
                        kind_choice = st.pills("Gig type", KIND_OPTIONS, selection_mode="single",
                                               label_visibility="collapsed", key="market_kind")

    st.space("small")
    with loading("Loading listings...", "Couldn't load the Marketplace.", key="retry_market"):
        entries = market.browse(query, chosen, kind_choice)
    render_listing_grid(entries, _open_listing, key_prefix="market")


# ------------------------------------------------------------ detail
def _render_detail(market, listing_id: int) -> None:
    with loading("Loading listing...", "Couldn't load this listing.", key="retry_detail"):
        entry = market.get_entry(listing_id)
    if entry is None:                      # deleted or closed in the meantime
        _close_listing()
        st.rerun()
        return

    back_col, _ = st.columns([1.4, 6], vertical_alignment="center")
    with back_col:
        st.button("Back to Marketplace", on_click=_close_listing, key="back_btn")

    main_col, side_col = st.columns([2.7, 1], gap="large")
    with main_col:
        render_listing_detail(entry)
    with side_col:
        render_side_panel(entry)


# ------------------------------------------------------------ entry
def render_marketplace() -> None:
    if render_open_profile("market"):
        return

    load_css("marketplace")
    market = get_marketplace_controller()
    view = _current_view()

    if view is _View.CREATE:
        render_create_listing()
    elif view is _View.BOOKING:
        render_booking_request(st.session_state.booking_listing_id)
    elif view is _View.DETAIL:
        _render_detail(market, st.session_state.selected_listing_id)
    else:
        _render_browse(market)


render_marketplace()