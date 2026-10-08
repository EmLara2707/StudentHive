"""Gigs / Rentals use-cases: what a user's transactions look like (lists, calendar,
to-dos) and the actions they can take (accept, reject, withdraw, complete, cancel,
review). Never imports streamlit."""
from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from models.review import Review
from models.transaction import (
    Counterpart, InvalidTransition, Role, TodoStep, TodoTask, Transaction,
    TransactionEntry, TransactionKind, TransactionStatus,
)

NOT_FOUND_ERROR = "This transaction is no longer available."
NOT_ALLOWED_ERROR = "That isn't available right now."
UNKNOWN_NAME = "Unknown student"
MAX_REVIEW_CHARS = 500


@dataclass
class ActionResult:
    ok: bool
    entry: TransactionEntry | None = None
    error: str = ""


class TransactionController:
    def __init__(self, transactions, users, reviews) -> None:
        self._transactions = transactions      # TransactionRepository
        self._users = users                    # UserRepository
        self._reviews = reviews                # ReviewRepository

    # ------------------------------------------------------------ loading
    def entries(self, email: str, kind: TransactionKind) -> list[TransactionEntry]:
        """All of this user's transactions of one kind (oldest id first)."""
        if not email:
            return []
        return [self._entry(t, email) for t in self._transactions.get_for_user(email, kind)]

    def get_entry(self, email: str, transaction_id: int | None,
                  kind: TransactionKind | None = None) -> TransactionEntry | None:
        """One transaction as `email` sees it, or None if it doesn't exist, isn't theirs
        or is the other kind."""
        if transaction_id is None:
            return None
        tx = self._transactions.get(transaction_id)
        if tx is None or not tx.involves(email) or (kind is not None and tx.kind is not kind):
            return None
        return self._entry(tx, email)

    def _entry(self, tx: Transaction, viewer_email: str) -> TransactionEntry:
        other = tx.counterpart_email(viewer_email)
        user = self._users.get_by_email(other)
        return TransactionEntry(tx, viewer_email, Counterpart(other, user.name if user else UNKNOWN_NAME))

    # ------------------------------------------------------------ tabs: filter + sort
    @staticmethod
    def active(entries: list[TransactionEntry], role: Role | None = None) -> list[TransactionEntry]:
        """My Gigs / My Rentals: accepted ones, optionally only one role."""
        return [e for e in entries
                if e.status is TransactionStatus.ACTIVE and (role is None or e.role is role)]

    @staticmethod
    def pending(entries: list[TransactionEntry], incoming: bool | None = None) -> list[TransactionEntry]:
        """incoming=True: requests to me (I'm the provider); False: requests I sent."""
        return [e for e in entries
                if e.status is TransactionStatus.PENDING
                and (incoming is None or e.is_provider == incoming)]

    @staticmethod
    def completed(entries: list[TransactionEntry], role: Role | None = None) -> list[TransactionEntry]:
        return [e for e in entries
                if e.status is TransactionStatus.COMPLETED and (role is None or e.role is role)]

    @staticmethod
    def cancelled(entries: list[TransactionEntry], by_me: bool | None = None) -> list[TransactionEntry]:
        return [e for e in entries
                if e.status is TransactionStatus.CANCELLED
                and (by_me is None or e.cancelled_by_me == by_me)]

    @staticmethod
    def sort_by_start(entries: list[TransactionEntry], ascending: bool) -> list[TransactionEntry]:
        return sorted(entries, key=lambda e: e.transaction.start, reverse=not ascending)

    @staticmethod
    def sort_by_end(entries: list[TransactionEntry], ascending: bool) -> list[TransactionEntry]:
        return sorted(entries, key=lambda e: e.transaction.end, reverse=not ascending)

    # ------------------------------------------------------------ calendar
    @staticmethod
    def by_day(entries: list[TransactionEntry]) -> dict[date, list[TransactionEntry]]:
        """Every entry listed under each day it covers. Within a day, the ones where I
        am the requester (Hiring / Renting, shown in green) come before the ones where
        I am the provider (Doing / Lending, orange); otherwise the order is unchanged."""
        grouped: dict[date, list[TransactionEntry]] = defaultdict(list)
        for e in entries:
            for day in e.transaction.days():
                grouped[day].append(e)
        for day_entries in grouped.values():
            day_entries.sort(key=lambda e: e.is_provider)      # False (requester) first, stable
        return grouped

    @staticmethod
    def on_day(entries: list[TransactionEntry], day: date) -> list[TransactionEntry]:
        return sorted((e for e in entries if e.transaction.covers(day)),
                      key=lambda e: e.transaction.start)

    # ------------------------------------------------------------ to-do list
    @staticmethod
    def todos(entries: list[TransactionEntry], today: date) -> list[TodoTask]:
        """Most urgent first: overdue, then soonest due. A pending request I must answer
        is due on its start date; an accepted one has a begin step (until it has
        started) and a finish step on its end date. Others' requests to wait on and
        finished or cancelled ones have no tasks."""
        tasks: list[TodoTask] = []
        for e in entries:
            tx = e.transaction
            if e.status is TransactionStatus.PENDING:
                if e.is_provider:
                    tasks.append(TodoTask(tx.start, TodoStep.RESPOND, e))
            elif e.status is TransactionStatus.ACTIVE:
                if tx.start >= today:
                    tasks.append(TodoTask(tx.start, TodoStep.BEGIN, e))
                tasks.append(TodoTask(tx.end, TodoStep.FINISH, e))
        tasks.sort(key=lambda t: t.due)
        return tasks

    @staticmethod
    def overdue_count(tasks: list[TodoTask], today: date) -> int:
        return sum(1 for t in tasks if t.due < today)

    # ------------------------------------------------------------ actions
    def accept(self, actor_email: str, transaction_id: int) -> ActionResult:
        return self._act(actor_email, transaction_id, lambda tx: tx.accept(actor_email))

    def reject(self, actor_email: str, transaction_id: int) -> ActionResult:
        return self._act(actor_email, transaction_id, lambda tx: tx.reject(actor_email))

    def withdraw(self, actor_email: str, transaction_id: int) -> ActionResult:
        return self._act(actor_email, transaction_id, lambda tx: tx.withdraw(actor_email))

    def complete(self, actor_email: str, transaction_id: int, today: date | None = None) -> ActionResult:
        today = today or date.today()
        return self._act(actor_email, transaction_id, lambda tx: tx.complete(actor_email, today))

    def cancel(self, actor_email: str, transaction_id: int, today: date | None = None) -> ActionResult:
        today = today or date.today()
        return self._act(actor_email, transaction_id, lambda tx: tx.cancel(actor_email, today))

    def _act(self, actor_email: str, transaction_id: int, change) -> ActionResult:
        entry = self.get_entry(actor_email, transaction_id)
        if entry is None:
            return ActionResult(False, error=NOT_FOUND_ERROR)
        try:
            change(entry.transaction)
        except InvalidTransition:
            return ActionResult(False, entry, NOT_ALLOWED_ERROR)
        self._transactions.save(entry.transaction)
        return ActionResult(True, entry)

    # ------------------------------------------------------------ reviews
    def can_review(self, actor_email: str, transaction_id: int) -> bool:
        entry = self.get_entry(actor_email, transaction_id)
        return (entry is not None
                and entry.status is TransactionStatus.COMPLETED
                and not entry.transaction.has_reviewed(actor_email))

    def submit_review(self, reviewer_email: str, transaction_id: int,
                      rating: int, text: str) -> ActionResult:
        """Leave a 1-5 star review for the other student (once per person per transaction)."""
        entry = self.get_entry(reviewer_email, transaction_id)
        if entry is None:
            return ActionResult(False, error=NOT_FOUND_ERROR)
        if not self.can_review(reviewer_email, transaction_id):
            return ActionResult(False, entry, NOT_ALLOWED_ERROR)
        if not 1 <= rating <= 5:
            return ActionResult(False, entry, "Please pick a star rating.")
        reviewer = self._users.get_by_email(reviewer_email)
        self._reviews.add(Review(
            reviewer=reviewer.name if reviewer else UNKNOWN_NAME,
            subject_email=entry.counterpart.email,
            rating=float(rating),
            text=(text or "").strip()[:MAX_REVIEW_CHARS],
        ))
        entry.transaction.mark_reviewed(reviewer_email)
        self._transactions.save(entry.transaction)
        return ActionResult(True, entry)