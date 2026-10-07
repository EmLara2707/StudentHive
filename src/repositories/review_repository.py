"""In-memory review storage."""
from models.review import Review
from repositories.user_repository import DEMO_EMAIL


class ReviewRepository:
    def __init__(self) -> None:
        self._reviews: list[Review] = []

    def add(self, review: Review) -> None:
        self._reviews.append(review)

    def get_for_user(self, email: str) -> list[Review]:
        key = email.strip().lower()
        return [r for r in self._reviews if r.subject_email == key]

    @classmethod
    def seeded(cls) -> "ReviewRepository":
        repo = cls()
        repo.add(Review("Student A", DEMO_EMAIL, 5.0, "Clear explanations and always on time."))
        repo.add(Review("Student B", DEMO_EMAIL, 5.0, "Helped me finally understand recursion."))
        return repo
