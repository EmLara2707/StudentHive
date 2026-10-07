"""Markup shared by the own-profile page and the public profile of other students.
Pure HTML helpers (plus one tiny st.markdown wrapper); styled by views/styles/profile.css."""
import html

import streamlit as st

from models.listing import Listing
from models.review import RatingSummary, Review


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
    return (f'<div class="pf-review"><b>{_e(review.reviewer)}</b> · ★ {review.rating:.1f}'
            f'<br>{_e(review.text)}</div>')


def render_reviews(reviews: list[Review]) -> None:
    if not reviews:
        st.markdown(empty_html("No reviews yet."), unsafe_allow_html=True)
    for review in reviews:
        st.markdown(review_html(review), unsafe_allow_html=True)
