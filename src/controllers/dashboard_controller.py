"""Dashboard rules: which listings and events to show. Never imports streamlit."""
from collections import defaultdict
from datetime import date

from models.event import CalendarEvent, EventKind

UPCOMING_LIMIT = 3


class DashboardController:
    def __init__(self, listings, events) -> None:
        self._listings = listings      # ListingRepository
        self._events = events          # EventRepository

    def get_listings(self, owner_email: str) -> list:
        return self._listings.get_by_owner(owner_email) if owner_email else []

    def get_events(self, owner_email: str) -> list[CalendarEvent]:
        return self._events.get_for_user(owner_email) if owner_email else []

    @staticmethod
    def group_by_day(events: list[CalendarEvent]) -> dict[date, list[CalendarEvent]]:
        grouped: dict[date, list[CalendarEvent]] = defaultdict(list)
        for e in events:
            grouped[e.date].append(e)
        return grouped

    @staticmethod
    def kinds(events: list[CalendarEvent]) -> set[EventKind]:
        return {e.kind for e in events}

    @staticmethod
    def upcoming(events: list[CalendarEvent], today: date,
                 limit: int = UPCOMING_LIMIT) -> list[CalendarEvent]:
        return [e for e in events if e.date >= today][:limit]

    @staticmethod
    def in_month(events: list[CalendarEvent], year: int, month: int) -> list[CalendarEvent]:
        return [e for e in events if (e.date.year, e.date.month) == (year, month)]
