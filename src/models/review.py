"""Review model (a rating one student leaves for another)."""
from dataclasses import dataclass


@dataclass
class Review:
    reviewer: str
    subject_email: str
    rating: float
    text: str


@dataclass(frozen=True)
class RatingSummary:
    average: float
    count: int
