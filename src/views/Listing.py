from dataclasses import dataclass, field
from typing import Callable, List, Optional

import streamlit as st

TEAL = "#0E8C7F"


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

    @property
    def price_label(self) -> str:
        return f"\u20b1{self.price:.0f}/{self.unit}"

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def render_image(self, height: int = 150, badge: bool = True) -> None:
        """Sky + hills placeholder with the category badge (pure CSS)."""
        badge_html = f"<span class='sh-badge'>{self.category}</span>" if badge else ""
        st.markdown(
            f"<div class='sh-image' style='height:{height}px'>"
            f"{badge_html}<div class='sh-cloud'></div></div>",
            unsafe_allow_html=True,
        )

    def render_card(self, on_view: Optional[Callable[[int], None]] = None,
                    key_prefix: str = "listing") -> None:
        """Marketplace card: image, title + price, divider, owner + View."""
        with st.container(key=f"listingcard_{key_prefix}_{self.id}"):
            self.render_image()
            st.markdown(
                f"<div class='sh-title-row'>"
                f"<div class='sh-card-title'>{self.title}</div>"
                f"<div class='sh-price'>{self.price_label}</div></div>"
                f"<hr class='sh-divider'>",
                unsafe_allow_html=True,
            )
            info_col, btn_col = st.columns([3, 1.3], vertical_alignment="center")
            with info_col:
                st.markdown(
                    f"<div class='sh-owner'>"
                    f"<div class='sh-avatar'>{self.owner[:1].upper()}</div>"
                    f"<div><div class='sh-owner-name'>{self.owner}</div>"
                    f"<div class='sh-owner-course'>{self.course}</div></div></div>",
                    unsafe_allow_html=True,
                )
            with btn_col:
                if on_view is not None:
                    st.button("View", key=f"{key_prefix}_view_{self.id}",
                              width="stretch", on_click=on_view, args=(self.id,))

    def render_detail(self) -> None:
        self.render_image(height=280)
        st.title(self.title)
        st.divider()
        st.subheader(f"About this {self.category}")
        for paragraph in self.description:
            st.write(paragraph)

        c1, c2 = st.columns(2)
        with c1, st.container(border=True):
            st.markdown("**Subjects Covered**")
            for s in self.subjects:
                st.write(f"- {s}")
        with c2, st.container(border=True):
            st.markdown("**Requirements**")
            for r in self.requirements:
                st.write(f"- {r}")

    def render_side_panel(self) -> None:
        with st.container(border=True):
            st.subheader(self.price_label)
            st.write(f"**{self.owner}**")
            st.caption(f"Course, {self.course}")
            st.button("Message Owner", width="stretch", disabled=True,
                      key=f"message_owner_{self.id}")
            st.button("Request Booking", width="stretch", disabled=True,
                      key=f"request_booking_{self.id}")


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