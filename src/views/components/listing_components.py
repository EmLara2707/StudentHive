"""Listing UI pieces: marketplace card, grid, detail page, gallery, lightbox.
Markup and widget keys are unchanged, so the CSS in Marketplace.py still applies.
Data comes from MarketplaceController as ListingEntry (listing + owner)."""
from html import escape
from typing import Callable, Optional

import streamlit as st

from models.listing import Listing, ListingEntry
from views.session import get_marketplace_controller

GALLERY_PREVIEW = 3   # tiles shown before the "+N" overlay


# ------------------------------------------------------------ callbacks
def open_profile(name: str) -> None:
    st.session_state.viewing_market_profile = name


def open_booking(listing_id: int) -> None:
    st.session_state.booking_listing_id = listing_id


# ------------------------------------------------------------ helpers
def _bg(uri: str) -> str:
    """Inline CSS that shows an uploaded photo as a covering background."""
    return f"background:url('{uri}') center/cover no-repeat;"


# ------------------------------------------------------------ marketplace card
def render_listing_image(listing: Listing, height: int = 150, badge: bool = True) -> None:
    """Sky + hills placeholder with the category badge (pure CSS)."""
    badge_html = ""
    if badge:
        kind = listing.deliverable_kind
        kind_html = f"<span class='sh-badge sh-badge-kind'>{escape(kind)}</span>" if kind else ""
        badge_html = (
            f"<div class='sh-badge-row'>"
            f"<span class='sh-badge sh-badge-{escape(listing.category.lower())}'>"
            f"{escape(listing.category)}</span>{kind_html}</div>"
        )
    cloud = "" if listing.images else "<div class='sh-cloud'></div>"
    photo = _bg(listing.images[0]) if listing.images else ""
    st.markdown(
        f"<div class='sh-image' style=\"height:{height}px;{photo}\">"
        f"{badge_html}{cloud}</div>",
        unsafe_allow_html=True,
    )


def render_listing_card(entry: ListingEntry, on_view: Optional[Callable[[int], None]] = None,
                        key_prefix: str = "listing") -> None:
    """Marketplace card: image, title + price, divider, owner + View."""
    listing, owner = entry.listing, entry.owner
    with st.container(key=f"listingcard_{key_prefix}_{listing.id}"):
        render_listing_image(listing)
        st.markdown(
            f"<div class='sh-title-row'>"
            f"<div class='sh-card-title'>{escape(listing.title)}</div>"
            f"<div class='sh-price'>{escape(listing.price_label)}</div></div>"
            f"<hr class='sh-divider'>",
            unsafe_allow_html=True,
        )
        info_col, btn_col = st.columns([3, 1.3], vertical_alignment="center")
        with info_col:
            st.markdown(
                f"<div class='sh-owner'>"
                f"<div class='sh-avatar'>{escape(owner.name[:1].upper())}</div>"
                f"<div><div class='sh-owner-name'>{escape(owner.name)}</div>"
                f"<div class='sh-owner-course'>{escape(owner.course)}</div></div></div>",
                unsafe_allow_html=True,
            )
        with btn_col:
            if on_view is not None:
                st.button("View", key=f"{key_prefix}_view_{listing.id}",
                          width="stretch", on_click=on_view, args=(listing.id,))


def render_listing_grid(entries: list[ListingEntry], on_view: Callable[[int], None],
                        key_prefix: str, columns: int = 3) -> None:
    """3-per-row card grid. Reuse on Marketplace, Gigs and Rentals pages."""
    if not entries:
        st.info("No listings match your search.")
        return
    for start in range(0, len(entries), columns):
        cols = st.columns(columns)
        for col, entry in zip(cols, entries[start:start + columns]):
            with col:
                render_listing_card(entry, on_view=on_view, key_prefix=key_prefix)


# ------------------------------------------------------------ detail page
def render_breadcrumb(listing: Listing) -> None:
    """'Marketplace > Title' next to the Back button."""
    st.markdown(
        f"<div class='sh-crumbs'>Marketplace<span>&gt;</span>{escape(listing.title)}</div>",
        unsafe_allow_html=True,
    )


def _gallery_tile(listing: Listing, i: int, size: str, extra: int = 0) -> None:
    if i >= len(listing.images):
        height = 368 if size == "big" else 176
        with st.container(key=f"galph_{listing.id}_{i}"):
            st.markdown(
                f"<div class='sh-image' style='height:{height}px;'><div class='sh-cloud'></div></div>",
                unsafe_allow_html=True,
            )
        return
    label = f"+{extra}" if extra else " "
    if st.button(label, key=f"gal_{size}_{listing.id}_{i}", width="stretch"):
        st.session_state.lb_index = i
        lightbox_dialog(listing.id)


def render_gallery(listing: Listing) -> None:
    total = len(listing.images)
    hidden = max(0, total - GALLERY_PREVIEW)

    # tile size per image: 3+ uses big + 2 thumbnails, fewer images use full-size tiles
    sizes = ["big", "thumb", "thumb"] if total >= 3 else ["big"] * total

    # one hidden block that sets each tile button's photo as its background
    rules = []
    for i, size in enumerate(sizes):
        shade = "linear-gradient(rgba(0,0,0,.55),rgba(0,0,0,.55)), " if (i == 2 and hidden) else ""
        rules.append(f".st-key-gal_{size}_{listing.id}_{i} button{{background-image:{shade}url('{listing.images[i]}');}}")
    with st.container(key="gal_css"):
        st.markdown(f"<style>{''.join(rules)}</style>", unsafe_allow_html=True)

    if total >= 3:
        # usual layout: one big tile + two stacked thumbnails (+N on the last one)
        big, side = st.columns([2, 1], gap="small")
        with big:
            _gallery_tile(listing, 0, "big")
        with side:
            _gallery_tile(listing, 1, "thumb")
            _gallery_tile(listing, 2, "thumb", extra=hidden)
    elif total == 2:
        # two halves
        left, right = st.columns(2, gap="small")
        with left:
            _gallery_tile(listing, 0, "big")
        with right:
            _gallery_tile(listing, 1, "big")
    else:
        # one image stretches across the full width
        # (with no images, this shows the full-width placeholder scene)
        _gallery_tile(listing, 0, "big")


def render_listing_detail(entry: ListingEntry) -> None:
    """Main column: gallery, title, meta line, About section."""
    listing, owner = entry.listing, entry.owner
    render_gallery(listing)
    meta = " &bull; ".join(escape(x) for x in
                           (owner.name, owner.course, listing.category, listing.deliverable) if x)
    paragraphs = "".join(
        f"<div class='sh-about-text'>{escape(p)}</div>" for p in listing.paragraphs
    ) or "<div class='sh-about-text'>No description provided.</div>"
    st.markdown(
        f"<div class='sh-detail-title'>{escape(listing.title)}</div>"
        f"<div class='sh-detail-meta'>{meta}</div>"
        f"<hr class='sh-detail-divider'>"
        f"<div class='sh-about-title'>About this {escape(listing.category)}</div>"
        f"{paragraphs}",
        unsafe_allow_html=True,
    )


def render_side_panel(entry: ListingEntry) -> None:
    """Right column: price, owner box, Message Owner / Request Booking."""
    listing, owner = entry.listing, entry.owner
    with st.container(key=f"detail_panel_{listing.id}"):
        per = "one-time payment" if listing.unit == "once" else f"/ {listing.unit_label}"
        cta = "Request Project" if listing.deliverable_kind == "Project" else "Request Booking"

        st.markdown(
            f"<div class='sh-panel-price'>"
            f"<span class='amt'>\u20b1{listing.price:.0f}</span>"
            f"<span class='per'>{escape(per)}</span></div>",
            unsafe_allow_html=True,
        )

        # clicking anywhere on the owner box opens their profile
        with st.container(key=f"profilerow_{listing.id}"):
            st.button("View profile", key=f"profilebtn_{listing.id}",
                      on_click=open_profile, args=(owner.name,))
            st.markdown(
                f"<div class='sh-panel-user'>"
                f"<div class='sh-avatar sh-avatar-lg'>{escape(owner.name[:1].upper())}</div>"
                f"<div><div class='sh-panel-user-name'>{escape(owner.name)}</div>"
                f"<div class='sh-panel-user-sub'>Course, {escape(owner.course)}</div></div></div>",
                unsafe_allow_html=True,
            )

        if st.button("Message Owner", key=f"message_owner_{listing.id}", width="stretch"):
            st.toast("Messaging is coming soon.")
        st.button(cta, key=f"request_booking_{listing.id}", width="stretch",
                  on_click=open_booking, args=(listing.id,))


# ------------------------------------------------------------ lightbox
def _lb_step(delta: int, n: int) -> None:
    st.session_state.lb_index = (st.session_state.get("lb_index", 0) + delta) % n


@st.dialog("Photos", width="large")
def lightbox_dialog(listing_id: int) -> None:
    entry = get_marketplace_controller().get_entry(listing_id)
    imgs = entry.listing.images if entry else []
    n = len(imgs)
    if n == 0:
        st.caption("No photos available.")
        return
    idx = st.session_state.get("lb_index", 0) % n
    left, mid, right = st.columns([1, 10, 1], vertical_alignment="center")
    left.button("", icon=":material/chevron_left:", key="lb_prev", on_click=_lb_step, args=(-1, n))
    mid.markdown(f'<img class="sh-lb-img" src="{imgs[idx]}">', unsafe_allow_html=True)
    right.button("", icon=":material/chevron_right:", key="lb_next", on_click=_lb_step, args=(1, n))
    mid.markdown(f'<div class="sh-lb-count">{idx + 1} / {n}</div>', unsafe_allow_html=True)
