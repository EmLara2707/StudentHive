"""What the controllers need from transaction storage. The only implementation is
SupabaseTransactionRepository; this file is just the interface."""
from typing import Protocol

from models.transaction import Transaction, TransactionKind, TransactionStatus


class TransactionRepository(Protocol):
    def add(self, transaction: Transaction) -> Transaction:
        """Store a new transaction; the database assigns the id."""
        ...

    def get(self, transaction_id: int) -> Transaction | None: ...

    def get_for_user(self, email: str, kind: TransactionKind | None = None) -> list[Transaction]: ...

    def save(self, transaction: Transaction, expected_status: TransactionStatus,
             expected_picked_up: bool = False, expected_dropped_off: bool = False) -> None:
        """Persist changes. `expected_*` is what was read (status, and for rentals whether
        pickup / drop-off were already confirmed): if someone else changed it meanwhile the
        save is refused (two people acting at once)."""
        ...


