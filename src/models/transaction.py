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

Pure data + rules: no Streamlit, no storage.
"""
from dataclasses import dataclass
from datetime import date, time, timedelta
from enum import Enum


PLACEHOLDER_IMAGE = "https://placehold.co/200"


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


class InvalidTransition(ValueError):
    """The requested status change is not allowed from the current state."""


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
        """Start time of an hourly booking ('4:00 PM'), otherwise 'All day'."""
        t = self.start_time if self.is_hourly else None
        if t is None:
            return "All day"
        return f"{t.hour % 12 or 12}:{t.minute:02d} {'AM' if t.hour < 12 else 'PM'}"

    def covers(self, day: date) -> bool:
        return self.start <= day <= self.end

    def days(self) -> list[date]:
        return [self.start + timedelta(days=i) for i in range(self.span_days)]

    def has_started(self, today: date) -> bool:
        return today >= self.start

    # ------------------------------------------------------------ what a viewer may do
    def allowed_actions(self, email: str, today: date) -> list[Action]:
        if not self.involves(email):
            return []
        if self.status is TransactionStatus.PENDING:
            if self.is_provider(email):
                return [Action.ACCEPT, Action.REJECT]
            return [Action.WITHDRAW]
        if self.status is TransactionStatus.ACTIVE:
            if self.has_started(today):
                return [Action.COMPLETE, Action.CANCEL]
            return [Action.CANCEL]
        return []

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

    def complete(self, by: str, today: date) -> None:
        self._require(Action.COMPLETE, by, today)
        self.status = TransactionStatus.COMPLETED

    def cancel(self, by: str, today: date) -> None:
        self._require(Action.CANCEL, by, today)
        self._cancel(by)

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


@dataclass(frozen=True)
class TodoTask:
    due: date
    step: TodoStep
    entry: TransactionEntry
