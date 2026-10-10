"""Review model (a rating one student leaves for another)."""
from dataclasses import dataclass


@dataclass
class Review:
    reviewer: str
    subject_email: str
    rating: float
    text: str
    reviewer_email: str = ""      # "" for the sample reviews; used to clean up on account deletion
    transaction_id: int | None = None   # None for the sample reviews


@dataclass(frozen=True)
class RatingSummary:
    average: float
    count: int

    @classmethod
    def from_reviews(cls, reviews: list[Review]) -> "RatingSummary":
        if not reviews:
            return cls(average=0.0, count=0)
        return cls(average=sum(r.rating for r in reviews) / len(reviews), count=len(reviews))
