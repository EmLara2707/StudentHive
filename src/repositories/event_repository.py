"""TEMPORARY in-memory calendar events for the Dashboard.
Replaced by Transactions (Gigs/Rentals) when those pages are restructured."""
from datetime import date, timedelta

from models.event import CalendarEvent, EventKind
from repositories.user_repository import DEMO_EMAIL

G, R = EventKind.GIG, EventKind.RENTAL

# (days from today, title, kind, time, price, unit)
_SAMPLES = [
    (1,  "Math Tutoring",            G, "4:00 PM",  150,  "hr"),
    (3,  "Studio Apartment viewing", R, "10:00 AM", 8000, "mo"),
    (3,  "Dog Walking",              G, "5:30 PM",  100,  "hr"),
    (6,  "Cleaning",                 G, "9:00 AM",  100,  "hr"),
    (9,  "Room move-in",             R, "1:00 PM",  5500, "mo"),
    (15, "Math Tutoring",            G, "4:00 PM",  150,  "hr"),
]


class EventRepository:
    def __init__(self) -> None:
        self._events: list[CalendarEvent] = []

    def add(self, event: CalendarEvent) -> None:
        self._events.append(event)

    def get_for_user(self, email: str) -> list[CalendarEvent]:
        owner = email.strip().lower()
        return sorted((e for e in self._events if e.owner_email == owner),
                      key=lambda e: e.date)

    @classmethod
    def seeded(cls, today: date | None = None) -> "EventRepository":
        """Sample events (demo user only), dated relative to today."""
        today = today or date.today()
        repo = cls()
        for offset, title, kind, time, price, unit in _SAMPLES:
            repo.add(CalendarEvent(DEMO_EMAIL, today + timedelta(days=offset),
                                   title, kind, time, price, unit))
        return repo
