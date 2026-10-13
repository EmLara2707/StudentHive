"""What the controllers need from listing storage. The only implementation is
SupabaseListingRepository; this file is just the interface."""
from typing import Protocol

from models.listing import Listing


class ListingRepository(Protocol):
    def get_all(self) -> list[Listing]:
        """Every listing, newest first."""
        ...

    def get_by_owner(self, owner_email: str) -> list[Listing]: ...

    def get(self, listing_id: int) -> Listing | None: ...

    def store_images(self, owner_email: str, images: list[tuple[bytes, str]]) -> list[str]:
        """Upload already-compressed (bytes, mime) images; returns what Listing.images holds."""
        ...

    def add(self, listing: Listing) -> Listing:
        """Insert a new listing. The database assigns the id."""
        ...

    def save(self, listing: Listing) -> None: ...

    def delete(self, listing_id: int) -> bool: ...
