"""Booking-request use-cases: load the listing being booked, price it,
validate the form and send the request (which becomes a pending Transaction
for the listing's owner to answer). Never imports streamlit."""
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

from controllers.marketplace_controller import MarketplaceController
from models.booking_request import (
    BookingContext, BookingForm, BookingKind, MeetingMode, PriceQuote, quote_price,
)
from models.listing import Listing
from models.review import RatingSummary
from models.transaction import (
    PLACEHOLDER_IMAGE, Transaction, TransactionKind, TransactionStatus,
)
from repositories.errors import ConflictError
from repositories.review_repository import ReviewRepository
from repositories.transaction_repository import TransactionRepository
from repositories.user_repository import UserRepository
from utils.clock import now_manila

COMING_SOON_MESSAGE = "Coming soon!"
OWN_LISTING_ERROR = "You can't book your own listing."
UNAVAILABLE_ERROR = "This listing is no longer available."
LOGIN_REQUIRED_ERROR = "Please log in to send a request."
DUPLICATE_ERROR = "You've already sent this request."
PAST_START_ERROR = "The start date can't be in the past."
PAST_TIME_ERROR = "The start time has already passed."
SAME_DAY_ERROR = "Hourly bookings must start and end on the same day."
END_BEFORE_START_ERROR = "The end date must be on or after the start date."
DATES_REQUIRED_ERROR = "Please choose a start and end date."

# Upper limits, so one request can't ask for years of calendar days (the Gigs and
# Rentals pages draw every day a booking covers).
MAX_BOOKING_DAYS = 90        # longest rental / one-time booking, start to end
MAX_DEADLINE_DAYS = 365      # furthest a project deadline can be


@dataclass
class BookingResult:
    ok: bool
    transaction: Transaction | None = None
    errors: list[str] = field(default_factory=list)


class BookingController:
    def __init__(
        self,
        market: MarketplaceController,
        reviews: ReviewRepository,
        transactions: TransactionRepository,
        users: UserRepository,
    ) -> None:
        self._market = market
        self._reviews = reviews
        self._transactions = transactions
        self._users = users

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

    def validate(self, context: BookingContext, form: BookingForm, requester_email: str,
                 today: date | None = None, now: datetime | None = None) -> list[str]:
        """Problems with the request, in the order they are shown (empty = valid).
        The form already limits most of these; they are checked here too so that no
        client can skip them."""
        if not self._users.exists(requester_email or ""):
            return [LOGIN_REQUIRED_ERROR]
        if not self.can_book(context.listing, requester_email):
            return [OWN_LISTING_ERROR]
        now = now or now_manila()
        today = today or now.date()
        clock = now.time()
        problems: list[str] = []
        if context.kind is BookingKind.PROJECT:
            if not form.details.strip():
                problems.append("Please describe your project.")
            if form.deadline is None or form.deadline < today:
                problems.append("The deadline can't be in the past.")
            elif form.deadline > today + timedelta(days=MAX_DEADLINE_DAYS):
                problems.append("The deadline can't be more than a year away.")
        else:
            if form.start_date is None or form.end_date is None:
                return [DATES_REQUIRED_ERROR]
            error = self.quote(context, form).error
            if error:
                problems.append(error)
            problems += self._schedule_problems(context.listing.unit, form, today, clock)
            if self._needs_location(context.kind, form) and not form.location.strip():
                problems.append("Please enter a proposed pickup / return location."
                                if context.kind is BookingKind.RENTAL
                                else "Please enter a meet-up location.")
        if not problems and self._is_duplicate(context, form, requester_email, today):
            problems.append(DUPLICATE_ERROR)
        return problems

    @staticmethod
    def _schedule_problems(unit: str, form: BookingForm, today: date, clock: time) -> list[str]:
        """Date rules the price quote doesn't cover (it already rejects an end before the
        start for daily and hourly bookings)."""
        problems: list[str] = []
        if form.start_date < today:
            problems.append(PAST_START_ERROR)
        elif unit == "hr" and form.start_date == today and form.start_time < clock:
            problems.append(PAST_TIME_ERROR)
        if unit == "hr" and form.end_date != form.start_date:
            problems.append(SAME_DAY_ERROR)
        if unit == "once" and form.end_date < form.start_date:
            problems.append(END_BEFORE_START_ERROR)
        if (form.end_date - form.start_date).days > MAX_BOOKING_DAYS:
            problems.append(f"A booking can be at most {MAX_BOOKING_DAYS} days long.")
        return problems

    def _is_duplicate(self, context: BookingContext, form: BookingForm,
                      requester_email: str, today: date) -> bool:
        """The same student asking for the same thing again while it is still open."""
        new = self._build_transaction(context, form, requester_email, today)
        same = lambda t: (t.listing_id, t.start, t.end, t.start_time, t.end_time,
                          t.deadline, t.project_details) == (
                          new.listing_id, new.start, new.end, new.start_time, new.end_time,
                          new.deadline, new.project_details)
        return any(
            t.status in (TransactionStatus.PENDING, TransactionStatus.ACTIVE) and same(t)
            for t in self._transactions.get_for_user(requester_email)
            if t.is_requester(requester_email)
        )

    # ---- sending ----
    def submit(self, listing_id: int, requester_email: str, form: BookingForm,
               today: date | None = None, now: datetime | None = None) -> BookingResult:
        context = self.get_context(listing_id)
        if context is None:
            return BookingResult(False, errors=[UNAVAILABLE_ERROR])
        now = now or now_manila()
        today = today or now.date()
        problems = self.validate(context, form, requester_email, today, now)
        if problems:
            return BookingResult(False, errors=problems)

        transaction = self._build_transaction(context, form, requester_email, today)
        try:
            return BookingResult(True, self._transactions.add(transaction))
        except ConflictError:       # the database's unique index: an identical open request
            return BookingResult(False, errors=[DUPLICATE_ERROR])

    def _build_transaction(self, context: BookingContext, form: BookingForm,
                           requester_email: str, today: date) -> Transaction:
        """The pending Transaction a valid request turns into."""
        listing = context.listing
        quote = self.quote(context, form)
        common = dict(
            id=0,
            kind=TransactionKind.GIG if listing.is_gig else TransactionKind.RENTAL,
            item=listing.title,
            image=listing.images[0] if listing.images else PLACEHOLDER_IMAGE,
            provider_email=listing.owner_email,
            requester_email=requester_email.strip().lower(),
            listing_id=listing.id,
        )
        if context.kind is BookingKind.PROJECT:
            # A project has no start/end: it runs from the request until the deadline.
            return Transaction(
                **common, start=today, end=form.deadline,
                price=listing.price, unit="once", quantity=1, total=quote.subtotal,
                project_details=form.details.strip(), deadline=form.deadline,
            )
        return Transaction(
            **common, start=form.start_date, end=form.end_date,
            price=listing.price, unit=listing.unit,
            quantity=quote.quantity, total=quote.subtotal,
            start_time=form.start_time if listing.unit == "hr" else None,
            end_time=form.end_time if listing.unit == "hr" else None,
            meeting_mode=form.meeting_mode.value if form.meeting_mode else None,
            location=(form.location.strip() if self._needs_location(context.kind, form) else ""),
        )

    @staticmethod
    def _needs_location(kind: BookingKind, form: BookingForm) -> bool:
        """Rentals always need a pickup/return place; Services only when meeting on campus."""
        return kind is BookingKind.RENTAL or (
            kind is BookingKind.SERVICE and form.meeting_mode is MeetingMode.CAMPUS
        )
