"""Read-only profile of another student: same layout as the Profile page, no edit controls.
Opened from the Marketplace, Gigs and Rentals pages.

Each of those pages starts with:
    if render_open_profile("market"):
        st.stop()
and opens a profile with open_profile(email, "market") as a button callback."""
import html

import streamlit as st

from models.public_profile import PublicProfile
from views.components.profile_components import (
    chip_html, empty_html, link_html, rating_html, render_reviews, thumb_html,
)
from views.components.styles import load_css
from views.session import get_public_profile_controller

_STATE_KEY = "viewing_profile"     # {"scope": page, "email": profile owner}


# ------------------------------------------------------------ navigation
def open_profile(email: str, scope: str) -> None:
    """Button callback: show this user's profile on the page named `scope`."""
    st.session_state[_STATE_KEY] = {"scope": scope, "email": email}


def close_profile() -> None:
    st.session_state.pop(_STATE_KEY, None)


def render_open_profile(scope: str) -> bool:
    """Draw the open profile if it belongs to this page; True means the page should stop."""
    target = st.session_state.get(_STATE_KEY)
    if not target or target["scope"] != scope:
        return False
    render_user_profile(target["email"], on_back=close_profile)
    return True


# ------------------------------------------------------------ sections
def _e(value) -> str:
    return html.escape(value or "")


def _heading(text: str) -> None:
    st.markdown(f'<div class="pf-h2">{_e(text)}</div>', unsafe_allow_html=True)


def _banner(p: PublicProfile) -> None:
    photo_url = p.profile.photo_url
    if photo_url:
        style, initial = f"background-image:url({html.escape(photo_url, quote=True)})", ""
    else:
        style, initial = "", _e(p.name[:1].upper())

    with st.container(key="banner"):
        with st.container(horizontal=True, vertical_alignment="center", key="banner_row"):
            with st.container(key="avatar"):
                st.markdown(f'<div class="pf-avatar" style="{style}">{initial}</div>', unsafe_allow_html=True)
            with st.container(key="banner_info"):
                st.markdown(f'<div class="pf-name">{_e(p.name)}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="pf-major">{_e(p.profile.major)}</div>', unsafe_allow_html=True)
                st.markdown(rating_html(p.rating), unsafe_allow_html=True)


def _about(p: PublicProfile) -> None:
    _heading("About me")
    with st.container(key="card_about"):
        if p.profile.bio:
            st.markdown(f'<div class="pf-about">{_e(p.profile.bio)}</div>', unsafe_allow_html=True)
        else:
            st.markdown(empty_html("No bio yet."), unsafe_allow_html=True)


def _portfolio(p: PublicProfile) -> None:
    _heading("Portfolio & Links")
    with st.container(key="card_portfolio"):
        st.markdown('<div class="pf-label">Personal Portfolio</div>'
                    f'<div class="pf-pill">{link_html(p.profile.portfolio)}</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.markdown('<div class="pf-label" style="margin-top:1rem">LinkedIn</div>'
                    f'<div class="pf-pill">{link_html(p.profile.linkedin)}</div>', unsafe_allow_html=True)
        c2.markdown('<div class="pf-label" style="margin-top:1rem">Github</div>'
                    f'<div class="pf-pill">{link_html(p.profile.github)}</div>', unsafe_allow_html=True)


def _socials(p: PublicProfile) -> None:
    _heading("Social Media Contacts")
    with st.container(key="card_socials"):
        st.markdown(chip_html(p.profile.socials, wide=True), unsafe_allow_html=True)


def _skills(p: PublicProfile) -> None:
    _heading("Skills")
    with st.container(key="card_skills"):
        st.markdown(chip_html(p.profile.skills), unsafe_allow_html=True)


def _listing_card(listing) -> None:
    with st.container(key=f"lcard_{listing.id}"):
        st.markdown(thumb_html(listing, listing.price_label), unsafe_allow_html=True)
        st.markdown(f'<div class="pf-listing-name">{_e(listing.title)}</div>', unsafe_allow_html=True)


def _tabs(p: PublicProfile) -> None:
    listings_tab, reviews_tab = st.tabs(["Listings", "Reviews"])
    with listings_tab:
        if not p.listings:
            st.markdown(empty_html("No listings yet."), unsafe_allow_html=True)
        else:
            with st.container(horizontal=True, key="listing_row"):
                for listing in p.listings:
                    _listing_card(listing)
    with reviews_tab:
        render_reviews(p.reviews)


# ------------------------------------------------------------ entry
def render_user_profile(email: str, on_back) -> None:
    """Draw another user's profile. `on_back` runs as the Back button's callback."""
    load_css("profile", "user_profile")
    st.button("← Back", key="up_back", on_click=on_back)

    profile = get_public_profile_controller().get(email)
    if profile is None:
        st.markdown(empty_html("This profile is no longer available."), unsafe_allow_html=True)
        return

    _banner(profile)
    _about(profile)
    portfolio_col, right_col = st.columns([1.5, 2.5])
    with portfolio_col:
        _portfolio(profile)
    with right_col:
        _socials(profile)
        _skills(profile)
    _tabs(profile)
