"""Markup shared by the own-profile page and the public profile of other students.
Pure HTML helpers (plus one tiny st.markdown wrapper); styled by views/styles/profile.css."""
import html

import streamlit as st

from models.listing import Listing
from models.review import (
    DEFAULT_REVIEW_SORT, REVIEW_FILTERS, REVIEW_SORTS, RatingSummary, Review,
)
from views.session import get_profile_controller


def _e(value) -> str:
    return html.escape(value or "")


def empty_html(text: str) -> str:
    return f'<div class="pf-empty">{_e(text)}</div>'


def chip_html(items, wide: bool = False) -> str:
    if not items:
        return empty_html("Nothing added yet.")
    cls = "pf-chip wide" if wide else "pf-chip"
    return "".join(f'<span class="{cls}">{_e(i)}</span>' for i in items)


def link_html(value: str) -> str:
    """A profile link as a clickable anchor when it is a web address, else plain text."""
    if not value:
        return "&nbsp;"
    safe = html.escape(value)
    if value.startswith(("http://", "https://")):
        return f'<a href="{safe}" target="_blank" rel="noopener noreferrer">{safe}</a>'
    return safe


def rating_html(summary: RatingSummary) -> str:
    if summary.count == 0:
        return '<div class="pf-rating">No reviews yet</div>'
    noun = "review" if summary.count == 1 else "reviews"
    return (f'<div class="pf-rating"><span class="star">★</span>'
            f'{summary.average:.1f} ({summary.count} {noun})</div>')


def thumb_html(listing: Listing, badge: str, closed: bool = False) -> str:
    """Listing cover (first photo, or the sky-and-hills placeholder) with a price badge."""
    cover = (
        f' style="background-image:url({listing.images[0]});background-size:cover;background-position:center"'
        if listing.images else ""
    )
    return (f'<div class="pf-thumb{" is-closed" if closed else ""}"{cover}>'
            f'<span class="pf-price">{_e(badge)}</span></div>')


def review_html(review: Review) -> str:
    role = {True: "as provider", False: "as customer"}.get(review.subject_is_provider)
    meta = " · ".join(x for x in (role, f"{review.created_at:%b} {review.created_at.day}, {review.created_at.year}"
                                  if review.created_at else None) if x)
    meta_html = f'<div class="pf-review-meta">{_e(meta)}</div>' if meta else ""
    return (f'<div class="pf-review"><b>{_e(review.reviewer)}</b> · ★ {review.rating:.1f}'
            f'<br>{_e(review.text)}{meta_html}</div>')


def render_reviews(reviews: list[Review], key: str = "own") -> None:
    """The Reviews tab: role pills (As provider / As customer, one at a time, none = all) and a
    sort dropdown (default: highest rated first). `key` keeps the widgets of different pages
    (own profile / each public profile) apart."""
    if not reviews:
        st.markdown(empty_html("No reviews yet."), unsafe_allow_html=True)
        return
    filt_col, sort_col = st.columns([3, 2], vertical_alignment="center")
    with filt_col:
        chosen = st.pills("Filter reviews", list(REVIEW_FILTERS), selection_mode="single",
                          label_visibility="collapsed", key=f"rvpills_{key}")
    with sort_col:
        sort = st.selectbox("Sort reviews", REVIEW_SORTS, index=REVIEW_SORTS.index(DEFAULT_REVIEW_SORT),
                            label_visibility="collapsed", key=f"rvsort_{key}")
    shown = get_profile_controller().sort_reviews(reviews, REVIEW_FILTERS.get(chosen), sort)
    if not shown:
        st.markdown(empty_html(f"No reviews {chosen.lower()} yet."), unsafe_allow_html=True)
    for review in shown:
        st.markdown(review_html(review), unsafe_allow_html=True)
