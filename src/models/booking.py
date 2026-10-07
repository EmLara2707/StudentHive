"""Booking request model.
TEMPORARY: bookings become pending Transactions when Gigs/Rentals are restructured."""
from dataclasses import dataclass, field


@dataclass
class Booking:
    id: int
    listing_id: int
    counterpart: str
    date: str
    status: str = "Pending"
    total: float = 0.0
    details: dict = field(default_factory=dict)
