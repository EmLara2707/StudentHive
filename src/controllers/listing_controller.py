"""Listing use-cases for owners: create, edit, close, reopen, delete.
Browsing and booking live in MarketplaceController. Never imports streamlit."""
from dataclasses import dataclass

from models.listing import (
    ALLOWED_MIMES, CATEGORIES, GIG, MAX_IMAGES, RATE_UNITS, Listing, ListingStatus,
)
from repositories.listing_repository import ListingRepository
from utils.images import compress_image


@dataclass
class ListingResult:
    ok: bool
    listing: Listing | None = None
    error: str | None = None


def _compress(images: list[tuple[bytes, str]]) -> list[tuple[bytes, str]]:
    """Compress raw uploads (bytes, mime); the repository decides how to store them."""
    out = []
    for raw, mime in images:
        data, out_mime = compress_image(raw, mime)
        out.append((data, out_mime if out_mime in ALLOWED_MIMES else "image/jpeg"))
    return out


class ListingController:
    def __init__(self, listings: ListingRepository) -> None:
        self._listings = listings

    def create(
        self,
        owner_email: str,
        title: str,
        category: str,
        rate_type: str,
        rate: float,
        description: str = "",
        deliverable: str = "",
        images: list[tuple[bytes, str]] | None = None,
    ) -> ListingResult:
        """Post a new listing (inserted first). Same rules as the create wizard:
        a category (and, for Gigs, a deliverable), a title, and a rate above 0."""
        if category not in CATEGORIES:
            return ListingResult(False, error="Please choose a listing type.")
        if category == GIG and not (deliverable or "").strip():
            return ListingResult(False, error="Please choose a deliverable type.")
        title = (title or "").strip()
        if not title:
            return ListingResult(False, error="Please add a title.")
        if rate is None or float(rate) <= 0:
            return ListingResult(False, error="Please enter a rate greater than 0.")
        if rate_type not in RATE_UNITS:
            return ListingResult(False, error="Please choose a rate type.")

        owner = (owner_email or "").strip().lower()
        listing = Listing(
            id=0,                      # assigned by the repository / database
            owner_email=owner,
            title=title,
            price=float(rate),
            category=category,
            deliverable=(deliverable or "").strip() if category == GIG else "",
            unit=RATE_UNITS[rate_type],
            description=(description or "").strip(),
            images=self._listings.store_images(owner, _compress((images or [])[:MAX_IMAGES])),
        )
        listing = self._listings.add(listing)
        return ListingResult(True, listing)

    def get_for_owner(self, owner_email: str) -> list[Listing]:
        return self._listings.get_by_owner(owner_email)

    def get(self, owner_email: str, listing_id: int) -> Listing | None:
        listing = self._listings.get(listing_id)
        if listing is None or listing.owner_email != owner_email.strip().lower():
            return None            # not found, or not yours
        return listing

    def update(
        self,
        owner_email: str,
        listing_id: int,
        title: str,
        rate_type: str,
        rate: float,
        description: str,
        kept_images: list[str],
        new_images: list[tuple[bytes, str]],
    ) -> str | None:
        """Apply an edit. Returns an error message, or None on success.
        Same rules as the create wizard: title required, rate > 0, max 10 images."""
        listing = self.get(owner_email, listing_id)
        if listing is None:
            return "This listing no longer exists."
        title = (title or "").strip()
        if not title:
            return "Please add a title."
        if rate is None or float(rate) <= 0:
            return "Please enter a rate greater than 0."
        if rate_type not in RATE_UNITS:
            return "Please choose a rate type."

        images = list(kept_images)[:MAX_IMAGES]
        room = MAX_IMAGES - len(images)
        images += self._listings.store_images(listing.owner_email, _compress(new_images[:room]))

        listing.title = title
        listing.unit = RATE_UNITS[rate_type]
        listing.price = float(rate)
        listing.description = (description or "").strip()
        listing.images = images
        self._listings.save(listing)
        return None

    def close(self, owner_email: str, listing_id: int) -> bool:
        return self._set_status(owner_email, listing_id, ListingStatus.CLOSED)

    def reopen(self, owner_email: str, listing_id: int) -> bool:
        return self._set_status(owner_email, listing_id, ListingStatus.OPEN)

    def delete(self, owner_email: str, listing_id: int) -> bool:
        if self.get(owner_email, listing_id) is None:
            return False
        return self._listings.delete(listing_id)

    def _set_status(self, owner_email: str, listing_id: int, status: ListingStatus) -> bool:
        listing = self.get(owner_email, listing_id)
        if listing is None:
            return False
        listing.status = status
        self._listings.save(listing)
        return True
