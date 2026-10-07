"""Calendar event: one day of an accepted Transaction, as the Dashboard shows it.
Derived from Transactions by DashboardController, never stored."""
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
    unit: str = "hr"          # "hr" | "day" | "once"

    @property
    def price_label(self) -> str:
        if self.unit == "once":
            return f"₱{self.price:,.0f}"
        return f"₱{self.price:,.0f}/{self.unit}"
