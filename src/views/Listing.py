import base64
from dataclasses import dataclass, field
from html import escape
from typing import Callable, List, Optional, Tuple

import streamlit as st

MAX_IMAGES = 10
GALLERY_PREVIEW = 3   # tiles shown before the "+N" overlay

ALLOWED_MIMES = ("image/jpeg", "image/png", "image/webp")


@dataclass
class Listing:
    """A single Gig or Rental posted on StudentHive."""
    id: int
    title: str
    category: str          # "Gig" or "Rental"
    price: float
    unit: str              # "hr" or "day"
    owner: str
    course: str
    description: List[str] = field(default_factory=list)
    subjects: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    deliverable: str = ""          # Gigs only: Service / Project Deliverables
    images: List[str] = field(default_factory=list)   # uploaded photos as data URIs (max 3)

    @staticmethod
    def _bg(uri: str) -> str:
        """Inline CSS that shows an uploaded photo as a covering background."""
        return f"background:url('{uri}') center/cover no-repeat;"

    @property
    def price_label(self):
        if self.unit == "once":
            return f"₱{self.price:,.0f}"
        return f"₱{self.price:,.0f}/{self.unit}"

    @property
    def unit_label(self):
        return {"hr": "hour", "day": "day", "once": "one-time"}.get(self.unit, self.unit)

    @property
    def deliverable_kind(self) -> str:
        """'Service' or 'Project' for Gigs, '' for Rentals."""
        if self.category != "Gig":
            return ""
        return "Project" if "project" in self.deliverable.lower() else "Service"

    # ------------------------------------------------------------------
    # Marketplace card
    # ------------------------------------------------------------------
    def render_image(self, height: int = 150, badge: bool = True) -> None:
        """Sky + hills placeholder with the category badge (pure CSS)."""
        badge_html = ""
        if badge:
            kind = self.deliverable_kind
            kind_html = f"<span class='sh-badge sh-badge-kind'>{escape(kind)}</span>" if kind else ""
            badge_html = (
                f"<div class='sh-badge-row'>"
                f"<span class='sh-badge sh-badge-{escape(self.category.lower())}'>"
                f"{escape(self.category)}</span>{kind_html}</div>"
            )
        cloud = "" if self.images else "<div class='sh-cloud'></div>"
        photo = self._bg(self.images[0]) if self.images else ""
        st.markdown(
            f"<div class='sh-image' style=\"height:{height}px;{photo}\">"
            f"{badge_html}{cloud}</div>",
            unsafe_allow_html=True,
        )

    def render_card(self, on_view: Optional[Callable[[int], None]] = None,
                    key_prefix: str = "listing") -> None:
        """Marketplace card: image, title + price, divider, owner + View."""
        with st.container(key=f"listingcard_{key_prefix}_{self.id}"):
            self.render_image()
            st.markdown(
                f"<div class='sh-title-row'>"
                f"<div class='sh-card-title'>{escape(self.title)}</div>"
                f"<div class='sh-price'>{escape(self.price_label)}</div></div>"
                f"<hr class='sh-divider'>",
                unsafe_allow_html=True,
            )
            info_col, btn_col = st.columns([3, 1.3], vertical_alignment="center")
            with info_col:
                st.markdown(
                    f"<div class='sh-owner'>"
                    f"<div class='sh-avatar'>{escape(self.owner[:1].upper())}</div>"
                    f"<div><div class='sh-owner-name'>{escape(self.owner)}</div>"
                    f"<div class='sh-owner-course'>{escape(self.course)}</div></div></div>",
                    unsafe_allow_html=True,
                )
            with btn_col:
                if on_view is not None:
                    st.button("View", key=f"{key_prefix}_view_{self.id}",
                              width="stretch", on_click=on_view, args=(self.id,))

    # ------------------------------------------------------------------
    # Listing detail page
    # ------------------------------------------------------------------
    def render_breadcrumb(self) -> None:
        """'Marketplace > Title' next to the Back button."""
        st.markdown(
            f"<div class='sh-crumbs'>Marketplace<span>&gt;</span>{escape(self.title)}</div>",
            unsafe_allow_html=True,
        )

    def render_gallery(self):
        total = len(self.images)
        hidden = max(0, total - GALLERY_PREVIEW)

        # tile size per image: 3+ uses big + 2 thumbnails, fewer images use full-size tiles
        sizes = ["big", "thumb", "thumb"] if total >= 3 else ["big"] * total

        # one hidden block that sets each tile button's photo as its background
        rules = []
        for i, size in enumerate(sizes):
            shade = "linear-gradient(rgba(0,0,0,.55),rgba(0,0,0,.55)), " if (i == 2 and hidden) else ""
            rules.append(f".st-key-gal_{size}_{self.id}_{i} button{{background-image:{shade}url('{self.images[i]}');}}")
        with st.container(key="gal_css"):
            st.markdown(f"<style>{''.join(rules)}</style>", unsafe_allow_html=True)

        if total >= 3:
            # usual layout: one big tile + two stacked thumbnails (+N on the last one)
            big, side = st.columns([2, 1], gap="small")
            with big:
                self._gallery_tile(0, "big")
            with side:
                self._gallery_tile(1, "thumb")
                self._gallery_tile(2, "thumb", extra=hidden)
        elif total == 2:
            # two halves
            left, right = st.columns(2, gap="small")
            with left:
                self._gallery_tile(0, "big")
            with right:
                self._gallery_tile(1, "big")
        else:
            # one image stretches across the full width
            # (with no images, this shows the full-width placeholder scene)
            self._gallery_tile(0, "big")

    def _gallery_tile(self, i, size, extra=0):
        if i >= len(self.images):
            height = 368 if size == "big" else 176
            with st.container(key=f"galph_{self.id}_{i}"):
                st.markdown(
                    f"<div class='sh-image' style='height:{height}px;'><div class='sh-cloud'></div></div>",
                    unsafe_allow_html=True,
                )
            return
        label = f"+{extra}" if extra else " "
        if st.button(label, key=f"gal_{size}_{self.id}_{i}", width="stretch"):
            st.session_state.lb_index = i
            lightbox_dialog(self.id)
    
    def render_detail(self) -> None:
        """Main column: gallery, title, meta line, About section."""
        self.render_gallery()
        meta = " &bull; ".join(escape(x) for x in
                               (self.owner, self.course, self.category, self.deliverable) if x)
        paragraphs = "".join(
            f"<div class='sh-about-text'>{escape(p)}</div>" for p in self.description
        ) or "<div class='sh-about-text'>No description provided.</div>"
        st.markdown(
            f"<div class='sh-detail-title'>{escape(self.title)}</div>"
            f"<div class='sh-detail-meta'>{meta}</div>"
            f"<hr class='sh-detail-divider'>"
            f"<div class='sh-about-title'>About this {escape(self.category)}</div>"
            f"{paragraphs}",
            unsafe_allow_html=True,
        )

    def render_side_panel(self) -> None:
        """Right column: price, owner box, Message Owner / Request Booking."""
        with st.container(key=f"detail_panel_{self.id}"):
            per = "one-time payment" if self.unit == "once" else f"/ {self.unit_label}"
            cta = "Request Project" if self.deliverable_kind == "Project" else "Request Booking"

            st.markdown(
                f"<div class='sh-panel-price'>"
                f"<span class='amt'>\u20b1{self.price:.0f}</span>"
                f"<span class='per'>{escape(per)}</span></div>"
                f"<div class='sh-panel-user'>"
                f"<div class='sh-avatar sh-avatar-lg'>{escape(self.owner[:1].upper())}</div>"
                f"<div><div class='sh-panel-user-name'>{escape(self.owner)}</div>"
                f"<div class='sh-panel-user-sub'>Course, {escape(self.course)}</div></div></div>",
                unsafe_allow_html=True,
            )
            if st.button("Message Owner", key=f"message_owner_{self.id}", width="stretch"):
                st.toast("Messaging is coming soon.")
            if st.button(cta, key=f"request_booking_{self.id}", width="stretch"):
                st.toast(f"{cta} is coming soon.")


@dataclass
class Booking:
    id: int
    listing_id: int
    counterpart: str
    date: str
    status: str = "Pending"   # Pending / Confirmed / Completed


class Marketplace:
    """Central data holder for listings and bookings."""

    def __init__(self) -> None:
        self._listings: List[Listing] = self._build_listings()
        self._bookings: List[Booking] = self._build_bookings()

    def _build_listings(self) -> List[Listing]:
        description = ["Lorem ipsum " * 5, "Lorem ipsum " * 15, "Lorem ipsum " * 10]
        subjects = ["Subject One", "Subject Two", "Subject Three", "Subject Four"]
        reqs = ["Requirement One", "Requirement Two", "Requirement Three", "Requirement Four"]
        rows = [
            (1, "Advanced Calculus Tutoring", "Gig", 300, "hr"),
            (2, "Dorm Room Mini Fridge Rental", "Rental", 150, "day"),
            (3, "Programming Fundamentals Tutoring", "Gig", 300, "hr"),
            (4, "Graphing Calculator Rental", "Rental", 150, "day"),
            (5, "Essay Editing & Proofreading", "Gig", 300, "hr"),
            (6, "Study Room Speaker Rental", "Rental", 150, "day"),
        ]
        return [Listing(i, t, c, p, u, "User", "MMCM", description, subjects, reqs)
                for i, t, c, p, u in rows]

    def _build_bookings(self) -> List[Booking]:
        return [
            Booking(1, 1, "User", "2026-10-05", "Confirmed"),
            Booking(2, 2, "User", "2026-10-08", "Pending"),
        ]

    def get_all_listings(self) -> List[Listing]:
        return self._listings

    def get_listing(self, listing_id: int) -> Optional[Listing]:
        return next((l for l in self._listings if l.id == listing_id), None)

    def get_by_category(self, category: str) -> List[Listing]:
        return [l for l in self._listings if l.category == category]

    def search(self, query: str = "", categories: Optional[List[str]] = None) -> List[Listing]:
        """Filter by text (title/owner/course) and by category list."""
        q = query.strip().lower()
        results = self._listings
        if categories:
            results = [l for l in results if l.category in categories]
        if q:
            results = [l for l in results
                       if q in l.title.lower() or q in l.owner.lower() or q in l.course.lower()]
        return results

    def add_listing(self, title: str, category: str, price: float,
                    course: str, owner: str, description: str = "",
                    unit: Optional[str] = None, deliverable: str = "",
                    images: Optional[List[Tuple[bytes, str]]] = None) -> Listing:
        """Create a new listing (newest first). Unit defaults to hr for Gigs, day for Rentals."""
        new_id = max((l.id for l in self._listings), default=0) + 1
        listing = Listing(
            id=new_id,
            title=title.strip(),
            category=category,
            price=price,
            unit=unit or ("hr" if category == "Gig" else "day"),
            owner=owner,
            course=course.strip() or "N/A",
            description=[description.strip()] if description.strip() else [],
            deliverable=deliverable,
            images=[
                f"data:{mime if mime in ALLOWED_MIMES else 'image/jpeg'};base64,"
                f"{base64.b64encode(raw).decode()}"
                for raw, mime in (images or [])[:MAX_IMAGES]
            ],
        )
        self._listings.insert(0, listing)
        return listing

    def get_gig_bookings(self) -> List[Booking]:
        return [b for b in self._bookings
                if self.get_listing(b.listing_id).category == "Gig"]

    def get_rental_bookings(self) -> List[Booking]:
        return [b for b in self._bookings
                if self.get_listing(b.listing_id).category == "Rental"]


def get_marketplace() -> Marketplace:
    """One Marketplace per session so it survives Streamlit reruns."""
    if "marketplace" not in st.session_state:
        st.session_state.marketplace = Marketplace()
    return st.session_state.marketplace


def render_listing_grid(listings: List[Listing],
                        on_view: Callable[[int], None],
                        key_prefix: str, columns: int = 3) -> None:
    """3-per-row card grid. Reuse on Marketplace, Gigs and Rentals pages."""
    if not listings:
        st.info("No listings match your search.")
        return
    for start in range(0, len(listings), columns):
        cols = st.columns(columns)
        for col, listing in zip(cols, listings[start:start + columns]):
            with col:
                listing.render_card(on_view=on_view, key_prefix=key_prefix)

def _lb_step(delta, n):
    st.session_state.lb_index = (st.session_state.get("lb_index", 0) + delta) % n

@st.dialog("Photos", width="large")
def lightbox_dialog(listing_id):
    listing = get_marketplace().get_listing(listing_id)
    imgs = listing.images
    n = len(imgs)
    idx = st.session_state.get("lb_index", 0) % n
    left, mid, right = st.columns([1, 10, 1], vertical_alignment="center")
    left.button("", icon=":material/chevron_left:", key="lb_prev", on_click=_lb_step, args=(-1, n))
    mid.markdown(f'<img class="sh-lb-img" src="{imgs[idx]}">', unsafe_allow_html=True)
    right.button("", icon=":material/chevron_right:", key="lb_next", on_click=_lb_step, args=(1, n))
    mid.markdown(f'<div class="sh-lb-count">{idx + 1} / {n}</div>', unsafe_allow_html=True)