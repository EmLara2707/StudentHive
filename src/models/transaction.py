"""A Transaction is one booking of a Gig or a Rental between two students.

The provider owns the listing (Doing a Gig / Lending a Rental); the requester
booked it (Hiring a Gig / Renting a Rental). Everything a page shows about "me"
and "them" is derived from those two emails, so there is one record per booking
no matter whose page it is shown on.

Lifecycle:
    Pending   -> Active     (provider accepts)
    Pending   -> Cancelled  (provider rejects, or requester withdraws)
    Active    -> Completed  (either side, once the start date has come)
    Active    -> Cancelled  (either side)

Rentals add two confirmations inside Active, each made by the side that receives the item:
    picked up   confirmed by the RENTER (from the start day on; until then either side may
                cancel, after it nobody can)
    dropped off confirmed by the LENDER once the item is back with them (any time after
                pickup); only then can the rental be completed or cancelled

Pure data + rules: no Streamlit, no storage.
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import Enum


PLACEHOLDER_IMAGE = "https://placehold.co/200"
REVIEW_WINDOW_DAYS = 14      # how long after completion a review can be left (also in migration 005)


class TransactionKind(str, Enum):
    GIG = "Gig"
    RENTAL = "Rental"


class TransactionStatus(str, Enum):
    PENDING = "Pending"
    ACTIVE = "Active"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class Role(str, Enum):
    """What the viewer is doing in a transaction (the value is the label shown)."""
    DOING = "Doing"          # Gig provider
    HIRING = "Hiring"        # Gig requester
    LENDING = "Lending"      # Rental provider
    RENTING = "Renting"      # Rental requester


_PROVIDER_ROLE = {TransactionKind.GIG: Role.DOING, TransactionKind.RENTAL: Role.LENDING}
_REQUESTER_ROLE = {TransactionKind.GIG: Role.HIRING, TransactionKind.RENTAL: Role.RENTING}


def provider_role(kind: TransactionKind) -> Role:
    return _PROVIDER_ROLE[kind]


def requester_role(kind: TransactionKind) -> Role:
    return _REQUESTER_ROLE[kind]


class Action(str, Enum):
    """Buttons the details panel can offer."""
    ACCEPT = "accept"          # provider answers a pending request
    REJECT = "reject"
    WITHDRAW = "withdraw"      # requester takes back a pending request
    COMPLETE = "complete"
    CANCEL = "cancel"
    CONFIRM_PICKUP = "confirm_pickup"      # rentals: the renter received the item
    CONFIRM_DROPOFF = "confirm_dropoff"    # rentals: the lender has the item back


class InvalidTransition(ValueError):
    """The requested status change is not allowed from the current state."""


def clock_label(t: time) -> str:
    """'4:00 PM'."""
    return f"{t.hour % 12 or 12}:{t.minute:02d} {'AM' if t.hour < 12 else 'PM'}"


def _key(email: str) -> str:
    return (email or "").strip().lower()


@dataclass
class Transaction:
    id: int
    kind: TransactionKind
    item: str
    image: str
    provider_email: str
    requester_email: str
    start: date
    end: date
    price: float                        # per `unit` (flat price when unit == "once")
    unit: str                           # "hr" | "day" | "once"
    quantity: float                     # billed days / hours (1 for one-time)
    total: float
    status: TransactionStatus = TransactionStatus.PENDING
    cancelled_by: str | None = None     # email of whoever cancelled / rejected / withdrew
    listing_id: int | None = None       # None for the sample history
    start_time: time | None = None      # hourly bookings only
    end_time: time | None = None
    meeting_mode: str | None = None     # Services only
    location: str = ""
    project_details: str = ""           # Projects only
    deadline: date | None = None        # Projects only
    completed_at: datetime | None = None   # when it became Completed (starts the review window)
    picked_up_at: datetime | None = None   # rentals: renter confirmed pickup
    dropped_off_at: datetime | None = None # rentals: renter confirmed drop-off

    # ------------------------------------------------------------ who is who
    def is_provider(self, email: str) -> bool:
        return _key(email) == _key(self.provider_email)

    def is_requester(self, email: str) -> bool:
        return _key(email) == _key(self.requester_email)

    def involves(self, email: str) -> bool:
        return self.is_provider(email) or self.is_requester(email)

    def role_for(self, email: str) -> Role:
        return provider_role(self.kind) if self.is_provider(email) else requester_role(self.kind)

    def counterpart_email(self, email: str) -> str:
        return self.requester_email if self.is_provider(email) else self.provider_email

    def cancelled_by_me(self, email: str) -> bool:
        return self.cancelled_by is not None and _key(self.cancelled_by) == _key(email)

    # ------------------------------------------------------------ derived values
    @property
    def price_label(self) -> str:
        if self.unit == "once":
            return f"₱{self.price:,.0f}"
        return f"₱{self.price:,.0f}/{self.unit}"

    @property
    def span_days(self) -> int:
        """Calendar days covered, counting both ends."""
        return (self.end - self.start).days + 1

    @property
    def is_hourly(self) -> bool:
        return self.unit == "hr"

    @property
    def time_label(self) -> str:
        """Start time ('4:00 PM'), or 'All day' when no time was stored (older bookings)."""
        t = self.start_time
        if t is None:
            return "All day"
        return clock_label(t)

    @property
    def is_rental(self) -> bool:
        return self.kind is TransactionKind.RENTAL

    @property
    def is_picked_up(self) -> bool:
        return self.picked_up_at is not None

    @property
    def is_dropped_off(self) -> bool:
        return self.dropped_off_at is not None

    def covers(self, day: date) -> bool:
        return self.start <= day <= self.end

    def days(self) -> list[date]:
        return [self.start + timedelta(days=i) for i in range(self.span_days)]

    def has_started(self, today: date) -> bool:
        return today >= self.start

    # ------------------------------------------------------------ review window
    @property
    def review_deadline(self) -> datetime | None:
        """Last moment a review can be left; None when unknown (no completion time stored)."""
        if self.completed_at is None:
            return None
        return self.completed_at + timedelta(days=REVIEW_WINDOW_DAYS)

    def review_open(self, now: datetime) -> bool:
        """True while a review can still be left (completed, and inside the window)."""
        if self.status is not TransactionStatus.COMPLETED:
            return False
        deadline = self.review_deadline
        return deadline is None or now <= deadline

    def review_days_left(self, now: datetime) -> int | None:
        """Whole days left to review, rounded up (so it never says 0 while still open)."""
        deadline = self.review_deadline
        if deadline is None or now > deadline:
            return None
        return max(1, -(-int((deadline - now).total_seconds()) // 86400))

    # ------------------------------------------------------------ what a viewer may do
    def allowed_actions(self, email: str, today: date) -> list[Action]:
        if not self.involves(email):
            return []
        if self.status is TransactionStatus.PENDING:
            if self.is_provider(email):
                return [Action.ACCEPT, Action.REJECT]
            return [Action.WITHDRAW]
        if self.status is TransactionStatus.ACTIVE:
            if self.is_rental:
                return self._rental_actions(email, today)
            if self.has_started(today):
                return [Action.COMPLETE, Action.CANCEL]
            return [Action.CANCEL]
        return []

    def _rental_actions(self, email: str, today: date) -> list[Action]:
        """Accepted rental: cancel until pickup is confirmed; no cancelling while the item is
        out; complete or cancel only once the lender has confirmed the drop-off.
        The renter confirms pickup (they receive the item); the lender confirms drop-off
        (they get it back), so neither side confirms both."""
        if self.is_dropped_off:
            return [Action.COMPLETE, Action.CANCEL]
        if self.is_picked_up:
            return [Action.CONFIRM_DROPOFF] if self.is_provider(email) else []
        if not self.has_started(today):
            return [Action.CANCEL]
        if self.is_requester(email):
            return [Action.CONFIRM_PICKUP, Action.CANCEL]    # got it, or didn't receive it
        return [Action.CANCEL]

    # ------------------------------------------------------------ transitions
    def accept(self, by: str) -> None:
        self._require(Action.ACCEPT, by)
        self.status = TransactionStatus.ACTIVE

    def reject(self, by: str) -> None:
        self._require(Action.REJECT, by)
        self._cancel(by)

    def withdraw(self, by: str) -> None:
        self._require(Action.WITHDRAW, by)
        self._cancel(by)

    def complete(self, by: str, today: date, now: datetime | None = None) -> None:
        self._require(Action.COMPLETE, by, today)
        self.status = TransactionStatus.COMPLETED
        self.completed_at = now

    def cancel(self, by: str, today: date) -> None:
        self._require(Action.CANCEL, by, today)
        self._cancel(by)

    def confirm_pickup(self, by: str, today: date, now: datetime | None = None) -> None:
        self._require(Action.CONFIRM_PICKUP, by, today)
        self.picked_up_at = now or datetime.combine(today, time())

    def confirm_dropoff(self, by: str, today: date, now: datetime | None = None) -> None:
        self._require(Action.CONFIRM_DROPOFF, by, today)
        self.dropped_off_at = now or datetime.combine(today, time())

    # ------------------------------------------------------------ internals
    def _cancel(self, by: str) -> None:
        self.status = TransactionStatus.CANCELLED
        self.cancelled_by = _key(by)

    def _require(self, action: Action, by: str, today: date | None = None) -> None:
        if action not in self.allowed_actions(by, today or self.start):
            raise InvalidTransition(f"Can't {action.value} a {self.status.value} transaction.")


@dataclass(frozen=True)
class Counterpart:
    email: str
    name: str


@dataclass(frozen=True)
class TransactionEntry:
    """A transaction seen from one user's side: who I am in it and who the other person is."""
    transaction: Transaction
    viewer_email: str
    counterpart: Counterpart
    can_review: bool = False      # completed, I haven't reviewed yet, and the window is open
    review_days_left: int | None = None   # days left to review (only while can_review)
    review_expired: bool = False  # completed, never reviewed by me, and the window has closed

    @property
    def id(self) -> int:
        return self.transaction.id

    @property
    def kind(self) -> TransactionKind:
        return self.transaction.kind

    @property
    def status(self) -> TransactionStatus:
        return self.transaction.status

    @property
    def role(self) -> Role:
        return self.transaction.role_for(self.viewer_email)

    @property
    def is_provider(self) -> bool:
        return self.transaction.is_provider(self.viewer_email)

    @property
    def cancelled_by_me(self) -> bool:
        return self.transaction.cancelled_by_me(self.viewer_email)

    def actions(self, today: date) -> list[Action]:
        return self.transaction.allowed_actions(self.viewer_email, today)


class TodoStep(str, Enum):
    RESPOND = "respond"      # a pending request I must answer
    BEGIN = "begin"          # the start date
    FINISH = "finish"        # the end date
    WRAP_UP = "wrap_up"      # rentals: the item is back, the rental can be completed


@dataclass(frozen=True)
class TodoTask:
    due: date
    step: TodoStep
    entry: TransactionEntry
