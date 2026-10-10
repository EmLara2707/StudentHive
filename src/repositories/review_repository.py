"""In-memory review storage."""
from models.review import Review
from repositories.errors import ConflictError
from repositories.seed_data import SAMPLE_REVIEWS, SAMPLE_STUDENTS
from repositories.user_repository import DEMO_EMAIL


class ReviewRepository:
    in_memory = True

    def __init__(self) -> None:
        self._reviews: list[Review] = []

    def add(self, review: Review) -> None:
        """Mirrors the database: one review per (transaction, reviewer)."""
        if (review.transaction_id is not None
                and self.has_reviewed(review.transaction_id, review.reviewer_email)):
            raise ConflictError()
        self._reviews.append(review)

    def has_reviewed(self, transaction_id: int, reviewer_email: str) -> bool:
        key = (reviewer_email or "").strip().lower()
        return any(r.transaction_id == transaction_id and r.reviewer_email == key
                   for r in self._reviews)

    def get_for_user(self, email: str) -> list[Review]:
        key = email.strip().lower()
        return [r for r in self._reviews if r.subject_email == key]

    def delete_for_user(self, email: str) -> int:
        """Remove every review written about the user; returns how many were removed."""
        key = email.strip().lower()
        kept = [r for r in self._reviews if r.subject_email != key]
        removed = len(self._reviews) - len(kept)
        self._reviews = kept
        return removed

    def delete_by_reviewer(self, email: str) -> int:
        """Remove every review the user wrote; returns how many were removed."""
        key = email.strip().lower()
        kept = [r for r in self._reviews if r.reviewer_email != key]
        removed = len(self._reviews) - len(kept)
        self._reviews = kept
        return removed

    @classmethod
    def seeded(cls) -> "ReviewRepository":
        repo = cls()
        repo.add(Review("Student A", DEMO_EMAIL, 5.0, "Clear explanations and always on time."))
        repo.add(Review("Student B", DEMO_EMAIL, 5.0, "Helped me finally understand recursion."))
        for s in SAMPLE_STUDENTS:
            for (reviewer, text), rating in zip(SAMPLE_REVIEWS, s.review_ratings):
                repo.add(Review(reviewer, s.email, rating, text))
        return repo
