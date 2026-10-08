"""Marketplace use-cases: browse and view listings (booking requests live in
BookingController). Never imports streamlit."""
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
    def __init__(self, listings, users) -> None:
        self._listings = listings      # ListingRepository
        self._users = users            # UserRepository

    # ---- owner display info ----
    def _entries(self, listings: list[Listing]) -> list[ListingEntry]:
        """Listings with their owners attached. Owners are loaded in ONE repository
        call for the whole list, not one lookup per card."""
        users = self._users.get_many({l.owner_email for l in listings})
        entries = []
        for listing in listings:
            user = users.get(listing.owner_email.strip().lower())
            if user is None:
                owner = OwnerInfo(listing.owner_email, UNKNOWN_OWNER, NO_COURSE)
            else:
                course = (user.profile.major or "").strip() or NO_COURSE
                owner = OwnerInfo(user.email, user.name, course)
            entries.append(ListingEntry(listing, owner))
        return entries

    # ---- browsing ----
    def get_entry(self, listing_id: int) -> ListingEntry | None:
        """An open listing with its owner, or None (missing, deleted or closed)."""
        listing = self._listings.get(listing_id)
        if listing is None or listing.is_closed:
            return None
        return self._entries([listing])[0]

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
        entries = self._entries([l for l in self._listings.get_all() if not l.is_closed])
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
