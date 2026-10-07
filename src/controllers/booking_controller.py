"""Booking-request use-cases: load the listing being booked, price it,
validate the form and send the request. Never imports streamlit."""
from dataclasses import dataclass, field
from datetime import date

from controllers.marketplace_controller import MarketplaceController
from models.booking import Booking
from models.booking_request import (
    BookingContext, BookingForm, BookingKind, MeetingMode, PriceQuote, quote_price,
)
from models.listing import Listing
from models.review import RatingSummary
from repositories.booking_repository import BookingRepository
from repositories.review_repository import ReviewRepository

COMING_SOON_MESSAGE = "Coming soon!"
OWN_LISTING_ERROR = "You can't book your own listing."
UNAVAILABLE_ERROR = "This listing is no longer available."


@dataclass
class BookingResult:
    ok: bool
    booking: Booking | None = None
    errors: list[str] = field(default_factory=list)


class BookingController:
    def __init__(
        self,
        market: MarketplaceController,
        reviews: ReviewRepository,
        bookings: BookingRepository,
    ) -> None:
        self._market = market
        self._reviews = reviews
        self._bookings = bookings      # TEMP: becomes pending Transactions later

    # ---- loading ----
    def get_context(self, listing_id: int) -> BookingContext | None:
        """The open listing with its owner and real rating, or None if it is gone."""
        entry = self._market.get_entry(listing_id)
        if entry is None:
            return None
        rating = RatingSummary.from_reviews(self._reviews.get_for_user(entry.owner.email))
        return BookingContext(entry, BookingKind.for_listing(entry.listing), rating)

    # ---- rules ----
    def can_book(self, listing: Listing, requester_email: str) -> bool:
        """Nobody can book their own listing."""
        return not listing.is_owned_by(requester_email)

    def rate_request_available(self, context: BookingContext) -> bool:
        """The main form button on daily / hourly Services and Rentals ("Request for
        Daily Rates" / "Request for Hourly Rates") is not available yet."""
        return context.kind is BookingKind.PROJECT or context.listing.unit not in ("day", "hr")

    def quote(self, context: BookingContext, form: BookingForm) -> PriceQuote:
        listing = context.listing
        if context.kind is BookingKind.PROJECT:
            return PriceQuote(None, listing.price)
        return quote_price(listing.unit, listing.price, form.start, form.end)

    def validate(self, context: BookingContext, form: BookingForm,
                 requester_email: str, today: date | None = None) -> list[str]:
        """Problems with the request, in the order they are shown (empty = valid)."""
        if not self.can_book(context.listing, requester_email):
            return [OWN_LISTING_ERROR]
        today = today or date.today()
        problems: list[str] = []
        if context.kind is BookingKind.PROJECT:
            if not form.details.strip():
                problems.append("Please describe your project.")
            if form.deadline is None or form.deadline < today:
                problems.append("The deadline can't be in the past.")
            return problems

        error = self.quote(context, form).error
        if error:
            problems.append(error)
        if self._needs_location(context.kind, form) and not form.location.strip():
            problems.append("Please enter a proposed pickup / return location."
                            if context.kind is BookingKind.RENTAL
                            else "Please enter a meet-up location.")
        return problems

    # ---- sending ----
    def submit(self, listing_id: int, requester_email: str, form: BookingForm,
               today: date | None = None) -> BookingResult:
        context = self.get_context(listing_id)
        if context is None:
            return BookingResult(False, errors=[UNAVAILABLE_ERROR])
        problems = self.validate(context, form, requester_email, today)
        if problems:
            return BookingResult(False, errors=problems)

        if context.kind is BookingKind.PROJECT:
            info = {"project_details": form.details.strip(),
                    "deadline": form.deadline.isoformat()}
            when = form.deadline.isoformat()
        else:
            info = {
                "start": form.start.isoformat(timespec="minutes"),
                "end": form.end.isoformat(timespec="minutes"),
                "meeting_mode": form.meeting_mode.value if form.meeting_mode else None,
                "location": (form.location.strip()
                             if self._needs_location(context.kind, form) else ""),
            }
            when = form.start_date.isoformat()
        total = self.quote(context, form).subtotal
        booking = self._bookings.add(context.listing.id, context.owner_name, when, total, info)
        return BookingResult(True, booking)

    @staticmethod
    def _needs_location(kind: BookingKind, form: BookingForm) -> bool:
        """Rentals always need a pickup/return place; Services only when meeting on campus."""
        return kind is BookingKind.RENTAL or (
            kind is BookingKind.SERVICE and form.meeting_mode is MeetingMode.CAMPUS
        )
