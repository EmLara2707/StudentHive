"""What the controllers need from review storage. The only implementation is
SupabaseReviewRepository; this file is just the interface."""
from typing import Protocol

from models.review import Review


class ReviewRepository(Protocol):
    def add(self, review: Review) -> None:
        """One review per (transaction, reviewer); a second raises ConflictError."""
        ...

    def has_reviewed(self, transaction_id: int, email: str) -> bool: ...

    def reviewed_ids(self, email: str) -> set[int]:
        """Ids of every transaction this person has already reviewed (one lookup)."""
        ...

    def get_for_user(self, email: str) -> list[Review]: ...
