"""TEMPORARY in-memory booking storage (replaced by Transactions later)."""
from models.booking import Booking


class BookingRepository:
    def __init__(self) -> None:
        self._items: list[Booking] = []

    def add(self, listing_id: int, counterpart: str, date: str,
            total: float = 0.0, details: dict | None = None) -> Booking:
        """Store a new booking request (newest first)."""
        new_id = max((b.id for b in self._items), default=0) + 1
        booking = Booking(new_id, listing_id, counterpart, date, "Pending", total, details or {})
        self._items.insert(0, booking)
        return booking

    def get_all(self) -> list[Booking]:
        return list(self._items)
