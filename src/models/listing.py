"""Listing domain model (a Gig or a Rental posted on StudentHive).
Pure data + behaviour: no Streamlit, no storage."""
from dataclasses import dataclass, field
from enum import Enum

MAX_IMAGES = 10
ALLOWED_MIMES = ("image/jpeg", "image/png", "image/webp")

GIG = "Gig"
RENTAL = "Rental"
CATEGORIES = (GIG, RENTAL)

SERVICE_DELIVERABLE = "Service Deliverables"
PROJECT_DELIVERABLE = "Project Deliverables"
DELIVERABLES = (SERVICE_DELIVERABLE, PROJECT_DELIVERABLE)

RATE_TYPES = ["Hourly Rate", "Daily Rate", "One Time Payment"]
RATE_UNITS = {"Hourly Rate": "hr", "Daily Rate": "day", "One Time Payment": "once"}
_RATE_TYPE_BY_UNIT = {unit: name for name, unit in RATE_UNITS.items()}
DEFAULT_GIG_RATE_TYPE = "Hourly Rate"
DEFAULT_RENTAL_RATE_TYPE = "Daily Rate"


def default_rate_type(category: str) -> str:
    """Rate type pre-selected for a new listing: Gigs hourly, Rentals daily."""
    return DEFAULT_GIG_RATE_TYPE if category == GIG else DEFAULT_RENTAL_RATE_TYPE


class ListingStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


@dataclass
class Listing:
    id: int
    owner_email: str                   # always lower-cased; owner name/course come from the user
    title: str
    price: float
    category: str = GIG                # "Gig" or "Rental"
    deliverable: str = ""              # Gigs only: "Service Deliverables" / "Project Deliverables"
    unit: str = "hr"                   # "hr" | "day" | "once"
    description: str = ""              # paragraphs separated by new lines
    images: list[str] = field(default_factory=list)   # image URLs (data URIs in the in-memory repository)
    status: ListingStatus = ListingStatus.OPEN

    @property
    def is_closed(self) -> bool:
        return self.status == ListingStatus.CLOSED

    def is_owned_by(self, email: str) -> bool:
        return self.owner_email == (email or "").strip().lower()

    @property
    def is_gig(self) -> bool:
        return self.category == GIG

    @property
    def is_rental(self) -> bool:
        return self.category == RENTAL

    @property
    def rate_type(self) -> str:
        return _RATE_TYPE_BY_UNIT.get(self.unit, "Hourly Rate")

    @property
    def price_label(self) -> str:
        if self.unit == "once":
            return f"₱{self.price:,.0f}"
        return f"₱{self.price:,.0f}/{self.unit}"

    @property
    def unit_label(self) -> str:
        return {"hr": "hour", "day": "day", "once": "one-time"}.get(self.unit, self.unit)

    @property
    def deliverable_kind(self) -> str:
        """'Service' or 'Project' for Gigs, '' for Rentals."""
        if not self.is_gig:
            return ""
        return "Project" if "project" in self.deliverable.lower() else "Service"

    @property
    def paragraphs(self) -> list[str]:
        return [p.strip() for p in self.description.splitlines() if p.strip()]


@dataclass(frozen=True)
class OwnerInfo:
    """Who posted a listing, as shown on cards and detail pages."""
    email: str
    name: str
    course: str


@dataclass(frozen=True)
class ListingEntry:
    """A listing together with its owner's display info."""
    listing: Listing
    owner: OwnerInfo
