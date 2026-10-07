"""Booking-request domain rules: what kind of request a listing takes, how the
price is worked out, and the data a request form carries.
Pure data + behaviour: no Streamlit, no storage."""
from dataclasses import dataclass
from datetime import date, datetime, time
from enum import Enum

from models.listing import Listing, ListingEntry
from models.review import RatingSummary


class BookingKind(str, Enum):
    """Which request layout a listing uses."""
    RENTAL = "Rental"        # dates + times + pickup/return location (always required)
    SERVICE = "Service"      # dates + times + meeting mode (location only On-Campus)
    PROJECT = "Project"      # project details + deadline, flat listing price

    @classmethod
    def for_listing(cls, listing: Listing) -> "BookingKind":
        if listing.is_rental:
            return cls.RENTAL
        return cls.PROJECT if listing.deliverable_kind == "Project" else cls.SERVICE


class MeetingMode(str, Enum):
    ONLINE = "Online Meeting"
    CAMPUS = "On-Campus"


@dataclass(frozen=True)
class PriceQuote:
    """Quantity is days or hours (1 for one-time), None when it doesn't apply or
    the dates are invalid. `error` explains an invalid date range."""
    quantity: float | None
    subtotal: float | None
    error: str | None = None


def quote_price(unit: str, price: float, start: datetime, end: datetime) -> PriceQuote:
    """Daily: whole days (at least 1, times ignored). Hourly: elapsed hours.
    One-time: price as is, dates don't matter."""
    if unit == "day":
        if end.date() < start.date():
            return PriceQuote(None, None, "The return date must be on or after the pickup date.")
        qty = max((end.date() - start.date()).days, 1)
    elif unit == "hr":
        secs = (end - start).total_seconds()
        if secs <= 0:
            return PriceQuote(None, None, "The end date and time must be after the start.")
        qty = round(secs / 3600, 2)
    else:
        qty = 1
    return PriceQuote(qty, price * qty)


@dataclass
class BookingForm:
    """Raw values from the request form. Which fields matter depends on the kind."""
    start_date: date | None = None
    start_time: time = time(10, 0)
    end_date: date | None = None
    end_time: time = time(10, 0)
    meeting_mode: MeetingMode | None = None      # Services only
    location: str = ""
    details: str = ""                            # Projects only
    deadline: date | None = None                 # Projects only

    @property
    def start(self) -> datetime:
        return datetime.combine(self.start_date, self.start_time)

    @property
    def end(self) -> datetime:
        return datetime.combine(self.end_date, self.end_time)


@dataclass(frozen=True)
class BookingContext:
    """Everything the request page shows about the listing being booked."""
    entry: ListingEntry
    kind: BookingKind
    owner_rating: RatingSummary

    @property
    def listing(self) -> Listing:
        return self.entry.listing

    @property
    def owner_name(self) -> str:
        return self.entry.owner.name
