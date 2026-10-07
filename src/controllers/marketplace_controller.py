"""Marketplace use-cases: browse, view a listing, send a booking request.
Never imports streamlit."""
from models.booking import Booking
from models.listing import GIG, RENTAL, Listing, ListingEntry, OwnerInfo

UNKNOWN_OWNER = "Unknown"
NO_COURSE = "N/A"

# The filter pills on the browse page, and what each one means for the data.
FILTER_GIG = "Gig"
FILTER_RENTALS = "Rentals"                  # the pill says "Rentals", the data says "Rental"
FILTER_OPTIONS = [FILTER_GIG, FILTER_RENTALS]
KIND_OPTIONS = ["Service", "Project"]       # only offered while the Gig pill is on
_CATEGORY_BY_FILTER = {FILTER_GIG: GIG, FILTER_RENTALS: RENTAL}


class MarketplaceController:
    def __init__(self, listings, users, bookings) -> None:
        self._listings = listings      # ListingRepository
        self._users = users            # UserRepository
        self._bookings = bookings      # BookingRepository

    # ---- owner display info ----
    def _owner(self, email: str) -> OwnerInfo:
        user = self._users.get_by_email(email)
        if user is None:
            return OwnerInfo(email, UNKNOWN_OWNER, NO_COURSE)
        course = (user.profile.major or "").strip() or NO_COURSE
        return OwnerInfo(user.email, user.name, course)

    def _entry(self, listing: Listing) -> ListingEntry:
        return ListingEntry(listing, self._owner(listing.owner_email))

    # ---- browsing ----
    def get_entry(self, listing_id: int) -> ListingEntry | None:
        """An open listing with its owner, or None (missing, deleted or closed)."""
        listing = self._listings.get(listing_id)
        if listing is None or listing.is_closed:
            return None
        return self._entry(listing)

    def search(
        self,
        query: str = "",
        categories: list[str] | None = None,
        deliverable_kind: str | None = None,
    ) -> list[ListingEntry]:
        """Open listings, newest first. Text matches title, owner or course;
        `categories` limits to Gig/Rental; `deliverable_kind` ("Service"/"Project")
        narrows Gigs."""
        q = (query or "").strip().lower()
        entries = [self._entry(l) for l in self._listings.get_all() if not l.is_closed]
        if categories:
            entries = [e for e in entries if e.listing.category in categories]
        if deliverable_kind:
            entries = [e for e in entries if e.listing.deliverable_kind == deliverable_kind]
        if q:
            entries = [
                e for e in entries
                if q in e.listing.title.lower() or q in e.owner.name.lower()
                or q in e.owner.course.lower()
            ]
        return entries

    def shows_kind_filter(self, filter_choice: str | None) -> bool:
        """Service / Project pills only make sense while the Gig pill is selected."""
        return filter_choice == FILTER_GIG

    def browse(
        self,
        query: str = "",
        filter_choice: str | None = None,
        kind_choice: str | None = None,
    ) -> list[ListingEntry]:
        """What the browse page shows, from its raw widget values: the search text,
        the selected pill (None = everything) and the selected Gig type. A Gig type
        left over from an earlier selection is ignored unless the Gig pill is on."""
        category = _CATEGORY_BY_FILTER.get(filter_choice)
        kind = kind_choice if self.shows_kind_filter(filter_choice) else None
        return self.search(query, [category] if category else None, deliverable_kind=kind)

    # ---- booking ----
    def add_booking(self, listing_id: int, date: str, total: float = 0.0,
                    details: dict | None = None) -> Booking | None:
        """Send a booking request for an open listing. None if it is no longer available."""
        entry = self.get_entry(listing_id)
        if entry is None:
            return None
        return self._bookings.add(listing_id, entry.owner.name, date, total, details)
