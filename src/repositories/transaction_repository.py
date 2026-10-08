"""In-memory transaction storage. Swap for a DB-backed class later; controllers
only depend on these method names."""
from datetime import date, timedelta

from models.transaction import (
    PLACEHOLDER_IMAGE, Transaction, TransactionKind, TransactionStatus,
)
from repositories.seed_data import email_for
from repositories.user_repository import DEMO_EMAIL

G, R = TransactionKind.GIG, TransactionKind.RENTAL
ACTIVE, PENDING = TransactionStatus.ACTIVE, TransactionStatus.PENDING
COMPLETED, CANCELLED = TransactionStatus.COMPLETED, TransactionStatus.CANCELLED

# (kind, item, demo user is the provider?, status, cancelled by "me"/"them"/None,
#  start offset, end offset (days from today), price per day, other student)
_SAMPLES = [
    # ---- Gigs ----
    (G, "Math Tutoring (Calculus)",  True,  ACTIVE,    None,   -3,  -1,  500, "Ana R."),
    (G, "Event Photography",         True,  ACTIVE,    None,    1,   4, 1200, "Miguel S."),
    (G, "Poster Design",             False, ACTIVE,    None,    0,   2,  400, "Carla D."),
    (G, "Thesis Proofreading",       False, ACTIVE,    None,    2,   3,  300, "Dan K."),
    (G, "Dog Walking",               True,  ACTIVE,    None,   12,  15,  250, "Nina T."),
    (G, "Guitar Lessons",            True,  PENDING,   None,    5,   7,  350, "Josh P."),
    (G, "Resume Review",             True,  PENDING,   None,    3,   4,  400, "Sam W."),
    (G, "Python Tutoring",           False, PENDING,   None,    9,  10,  450, "Leo M."),
    (G, "Video Editing",             True,  COMPLETED, None,  -20, -18,  800, "Rico B."),
    (G, "Logo Design",               False, COMPLETED, None,  -14, -11,  600, "Mia L."),
    (G, "Essay Editing",             True,  COMPLETED, None,   -9,  -8,  200, "Ana R."),
    (G, "Wedding Videography",       True,  CANCELLED, "me",   -6,  -5, 1500, "Paolo G."),
    (G, "Social Media Management",   False, CANCELLED, "them", -2,  -1,  350, "Kyla V."),
    # ---- Rentals ----
    (R, "Canon DSLR Camera",         False, ACTIVE,    None,   -3,  -1,  500, "Ana R."),
    (R, "Camping Tent (4P)",         False, ACTIVE,    None,    1,   4,  350, "Miguel S."),
    (R, "Projector",                 True,  ACTIVE,    None,    0,   2,  400, "Carla D."),
    (R, "Portable Speaker",          True,  ACTIVE,    None,    2,   3,  180, "Dan K."),
    (R, "Folding Bike",              True,  ACTIVE,    None,   12,  15,  250, "Nina T."),
    (R, "Electric Guitar",           True,  PENDING,   None,    5,   7,  300, "Josh P."),
    (R, "Gaming Console",            True,  PENDING,   None,    3,   4,  350, "Sam W."),
    (R, "Power Drill",               False, PENDING,   None,    9,  10,  150, "Leo M."),
    (R, "Karaoke Set",               False, COMPLETED, None,  -20, -18,  600, "Rico B."),
    (R, "Acoustic Guitar",           True,  COMPLETED, None,  -14, -11,  200, "Mia L."),
    (R, "Tripod Stand",              False, COMPLETED, None,   -9,  -8,  100, "Ana R."),
    (R, "Sound System",              False, CANCELLED, "me",   -6,  -5,  800, "Paolo G."),
    (R, "Ring Light",                True,  CANCELLED, "them", -2,  -1,  120, "Kyla V."),
]


class TransactionRepository:
    def __init__(self) -> None:
        self._items: list[Transaction] = []

    def next_id(self) -> int:
        return max((t.id for t in self._items), default=0) + 1

    def add(self, transaction: Transaction) -> Transaction:
        """Store a new transaction and give it its id."""
        transaction.id = self.next_id()
        self._items.append(transaction)
        return transaction

    def get(self, transaction_id: int) -> Transaction | None:
        return next((t for t in self._items if t.id == transaction_id), None)

    def get_for_user(self, email: str, kind: TransactionKind | None = None) -> list[Transaction]:
        """Every transaction the user is part of, oldest id first."""
        return [t for t in self._items
                if t.involves(email) and (kind is None or t.kind is kind)]

    def delete_for_user(self, email: str) -> int:
        """Remove every transaction the user is part of; returns how many were removed."""
        kept = [t for t in self._items if not t.involves(email)]
        removed = len(self._items) - len(kept)
        self._items = kept
        return removed

    def save(self, transaction: Transaction) -> None:
        """Persist changes to an existing transaction (a DB repo would UPDATE here)."""
        for i, existing in enumerate(self._items):
            if existing.id == transaction.id:
                self._items[i] = transaction
                return
        raise KeyError(transaction.id)

    @classmethod
    def seeded(cls, today: date | None = None) -> "TransactionRepository":
        """Sample history for the demo user, dated relative to today."""
        today = today or date.today()
        repo = cls()
        for kind, item, is_provider, status, cancelled, a, b, price, other in _SAMPLES:
            other_email = email_for(other)
            provider, requester = ((DEMO_EMAIL, other_email) if is_provider
                                   else (other_email, DEMO_EMAIL))
            start, end = today + timedelta(days=a), today + timedelta(days=b)
            quantity = (end - start).days + 1
            cancelled_by = {"me": DEMO_EMAIL, "them": other_email}.get(cancelled)
            repo.add(Transaction(
                id=0, kind=kind, item=item, image=PLACEHOLDER_IMAGE,
                provider_email=provider, requester_email=requester,
                start=start, end=end, price=price, unit="day",
                quantity=quantity, total=price * quantity,
                status=status, cancelled_by=cancelled_by,
            ))
        return repo
