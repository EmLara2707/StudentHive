"""Review model (a rating one student leaves for another)."""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Review:
    reviewer: str
    subject_email: str
    rating: float
    text: str
    reviewer_email: str = ""      # "" for the sample reviews; used to clean up on account deletion
    transaction_id: int | None = None   # None for the sample reviews
    created_at: datetime | None = None  # None for the sample reviews
    subject_is_provider: bool | None = None   # True: the reviewed person was the provider
                                              # (doing the gig / lending); False: the customer;
                                              # None for the sample reviews


@dataclass(frozen=True)
class RatingSummary:
    average: float
    count: int

    @classmethod
    def from_reviews(cls, reviews: list[Review]) -> "RatingSummary":
        if not reviews:
            return cls(average=0.0, count=0)
        return cls(average=sum(r.rating for r in reviews) / len(reviews), count=len(reviews))


# ---- sorting / filtering of a profile's reviews tab ----
REVIEW_FILTERS = {"As provider": True, "As customer": False}   # pill label -> subject_is_provider
REVIEW_SORTS = ["★ Highest rated", "★ Lowest rated", "↓ Newest first", "↑ Oldest first"]
DEFAULT_REVIEW_SORT = REVIEW_SORTS[0]


def _when(review: Review) -> float:
    return review.created_at.timestamp() if review.created_at else float("-inf")


def filter_and_sort_reviews(reviews: list[Review], as_provider: bool | None = None,
                            sort: str = DEFAULT_REVIEW_SORT) -> list[Review]:
    """as_provider True/False keeps only reviews of that role; None keeps everything. Reviews
    with no role (the sample ones) only show when nothing is filtered. Ties on rating go to the
    newer review; reviews with no date count as the oldest."""
    kept = [r for r in reviews if as_provider is None or r.subject_is_provider is as_provider]
    if sort == "★ Lowest rated":
        return sorted(kept, key=lambda r: (r.rating, -_when(r)))
    if sort == "↓ Newest first":
        return sorted(kept, key=_when, reverse=True)
    if sort == "↑ Oldest first":
        return sorted(kept, key=_when)
    return sorted(kept, key=lambda r: (-r.rating, -_when(r)))      # Highest rated (default)
