"""TEMPORARY in-memory listing storage for the Profile page.
Replaced by the real ListingRepository when we restructure Listing.py."""
from models.listing import ListingSummary
from repositories.user_repository import DEMO_EMAIL

SERVICE, PROJECT = "Service Deliverables", "Project Deliverables"

# (title, price, category, deliverable, unit, description)
_SAMPLES = [
    ("Python Tutoring", 20, "Gig", SERVICE, "hr", "One-on-one Python tutoring for beginners."),
    ("Figma Design Review", 25, "Gig", SERVICE, "hr", "Feedback on your Figma layouts and prototypes."),
    ("Calculus Help", 18, "Gig", SERVICE, "hr", "Help with limits, derivatives and integrals."),
    ("Resume Workshop", 15, "Gig", SERVICE, "hr", "Polish your resume and cover letter."),
    ("Guitar Lessons", 30, "Gig", SERVICE, "hr", "Acoustic guitar lessons for all levels."),
    ("Essay Proofreading", 12, "Gig", PROJECT, "once", "Grammar and clarity pass on your essay."),
    ("Camera Rental", 40, "Rental", "", "day", "DSLR camera with a kit lens and bag."),
    ("Spanish Conversation", 22, "Gig", SERVICE, "hr", "Practice conversational Spanish."),
]


class ListingRepository:
    def __init__(self) -> None:
        self._items: dict[int, ListingSummary] = {}

    def get_by_owner(self, owner_email: str) -> list[ListingSummary]:
        owner = owner_email.strip().lower()
        return [l for l in self._items.values() if l.owner_email == owner]

    def get(self, listing_id: int) -> ListingSummary | None:
        return self._items.get(listing_id)

    def save(self, listing: ListingSummary) -> None:
        self._items[listing.id] = listing

    def delete(self, listing_id: int) -> bool:
        return self._items.pop(listing_id, None) is not None

    @classmethod
    def seeded(cls) -> "ListingRepository":
        repo = cls()
        for i, (title, price, category, deliverable, unit, desc) in enumerate(_SAMPLES, start=1):
            repo.save(ListingSummary(
                id=i, owner_email=DEMO_EMAIL, title=title, price=price,
                category=category, deliverable=deliverable, unit=unit, description=desc,
            ))
        return repo
