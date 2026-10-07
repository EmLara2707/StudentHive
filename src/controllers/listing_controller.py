"""TEMPORARY listing use-cases for the Profile page (edit / close / reopen / delete).
Will be merged with the marketplace listing controller when Listing.py is restructured."""
from models.listing import MAX_IMAGES, RATE_UNITS, ListingStatus, ListingSummary
from repositories.listing_repository import ListingRepository
from utils.images import compress_image, to_data_uri


class ListingController:
    def __init__(self, listings: ListingRepository) -> None:
        self._listings = listings

    def get_for_owner(self, owner_email: str) -> list[ListingSummary]:
        return self._listings.get_by_owner(owner_email)

    def get(self, owner_email: str, listing_id: int) -> ListingSummary | None:
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
        for raw, mime in new_images:
            if len(images) >= MAX_IMAGES:
                break
            images.append(to_data_uri(*compress_image(raw, mime)))

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
