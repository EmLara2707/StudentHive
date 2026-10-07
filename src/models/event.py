"""Calendar event model.
TEMPORARY: once Gigs/Rentals are restructured, events will be derived from
active Transactions instead of being stored on their own."""
from dataclasses import dataclass
from datetime import date
from enum import Enum


class EventKind(str, Enum):
    GIG = "Gig"
    RENTAL = "Rental"


@dataclass(frozen=True)
class CalendarEvent:
    owner_email: str
    date: date
    title: str
    kind: EventKind
    time: str
    price: float
    unit: str = "hr"          # "hr" | "day" | "mo" | ...

    @property
    def price_label(self) -> str:
        return f"₱{self.price:,.0f}/{self.unit}"
