"""TEMPORARY listing model used by the Profile page's "My Listings" row.
It mirrors the fields of the real Listing and will be merged into it when we
restructure Listing.py / CreateListing.py (which should import the constants below)."""
from dataclasses import dataclass, field
from enum import Enum

MAX_IMAGES = 10
RATE_TYPES = ["Hourly Rate", "Daily Rate", "One Time Payment"]
RATE_UNITS = {"Hourly Rate": "hr", "Daily Rate": "day", "One Time Payment": "once"}
_RATE_TYPE_BY_UNIT = {unit: name for name, unit in RATE_UNITS.items()}


class ListingStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


@dataclass
class ListingSummary:
    id: int
    owner_email: str
    title: str
    price: float
    category: str = "Gig"              # "Gig" or "Rental"
    deliverable: str = ""              # Gigs only
    unit: str = "hr"                   # "hr" | "day" | "once"
    description: str = ""
    images: list[str] = field(default_factory=list)   # data URIs
    status: ListingStatus = ListingStatus.OPEN

    @property
    def is_closed(self) -> bool:
        return self.status == ListingStatus.CLOSED

    @property
    def rate_type(self) -> str:
        return _RATE_TYPE_BY_UNIT.get(self.unit, "Hourly Rate")

    @property
    def price_label(self) -> str:
        amount = f"{self.price:g}"
        return {"hr": f"{amount}/hr", "day": f"{amount}/day"}.get(self.unit, f"{amount} one-time")
