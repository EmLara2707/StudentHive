"""What another student sees when they open someone's profile."""
from dataclasses import dataclass, field

from models.listing import Listing
from models.profile import Profile
from models.review import RatingSummary, Review


@dataclass(frozen=True)
class PublicProfile:
    name: str
    email: str
    profile: Profile
    rating: RatingSummary
    reviews: list[Review] = field(default_factory=list)
    listings: list[Listing] = field(default_factory=list)   # open listings only
