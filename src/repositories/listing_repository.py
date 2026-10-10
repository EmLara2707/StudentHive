"""In-memory listing storage. Swap this class for a DB-backed one later;
controllers only depend on these method names."""
from models.listing import ALLOWED_MIMES, GIG, RENTAL, Listing
from utils.images import to_data_uri
from repositories.user_repository import DEMO_EMAIL, SAMPLE_SELLER_EMAIL

SERVICE, PROJECT = "Service Deliverables", "Project Deliverables"

# Demo user's own listings (Profile / Dashboard):
# (title, price, category, deliverable, unit, description)
_DEMO_SAMPLES = [
    ("Python Tutoring", 20, GIG, SERVICE, "hr", "One-on-one Python tutoring for beginners."),
    ("Figma Design Review", 25, GIG, SERVICE, "hr", "Feedback on your Figma layouts and prototypes."),
    ("Calculus Help", 18, GIG, SERVICE, "hr", "Help with limits, derivatives and integrals."),
    ("Resume Workshop", 15, GIG, SERVICE, "hr", "Polish your resume and cover letter."),
    ("Guitar Lessons", 30, GIG, SERVICE, "hr", "Acoustic guitar lessons for all levels."),
    ("Essay Proofreading", 12, GIG, PROJECT, "once", "Grammar and clarity pass on your essay."),
    ("Camera Rental", 40, RENTAL, "", "day", "DSLR camera with a kit lens and bag."),
    ("Spanish Conversation", 22, GIG, SERVICE, "hr", "Practice conversational Spanish."),
]

# Sample marketplace listings from another student:
# (title, category, price, unit, deliverable)
_MARKET_SAMPLES = [
    ("Advanced Calculus Tutoring", GIG, 300, "hr", SERVICE),
    ("Dorm Room Mini Fridge Rental", RENTAL, 150, "day", ""),
    ("Programming Fundamentals Tutoring", GIG, 300, "hr", SERVICE),
    ("Graphing Calculator Rental", RENTAL, 150, "day", ""),
    ("Essay Editing & Proofreading", GIG, 300, "once", PROJECT),
    ("Study Room Speaker Rental", RENTAL, 150, "day", ""),
    ("Poster & Slide Deck Design", GIG, 500, "once", PROJECT),
]
_MARKET_DESCRIPTION = "\n".join(
    ["Lorem ipsum " * 5, "Lorem ipsum " * 15, "Lorem ipsum " * 10]
).replace(" \n", "\n").strip()


class ListingRepository:
    in_memory = True

    def __init__(self) -> None:
        self._items: dict[int, Listing] = {}

    def get_all(self) -> list[Listing]:
        """Every listing, newest first."""
        return list(self._items.values())

    def get_by_owner(self, owner_email: str) -> list[Listing]:
        owner = owner_email.strip().lower()
        return [l for l in self._items.values() if l.owner_email == owner]

    def get(self, listing_id: int) -> Listing | None:
        return self._items.get(listing_id)

    def next_id(self) -> int:
        return max(self._items, default=0) + 1

    def store_images(self, owner_email: str, images: list[tuple[bytes, str]]) -> list[str]:
        """Turn already-compressed (bytes, mime) images into what Listing.images holds.
        In memory that is a data URI; the Supabase repository uploads and returns URLs."""
        return [to_data_uri(data, mime if mime in ALLOWED_MIMES else "image/jpeg")
                for data, mime in images]

    def add(self, listing: Listing) -> Listing:
        """Insert a new listing at the front (newest first). Like the database, this
        assigns the id (any id on the listing passed in is replaced)."""
        listing.id = self.next_id()
        self._items = {listing.id: listing, **self._items}
        return listing

    def save(self, listing: Listing) -> None:
        """Persist changes to an existing listing."""
        self._items[listing.id] = listing

    def delete(self, listing_id: int) -> bool:
        return self._items.pop(listing_id, None) is not None

    @classmethod
    def seeded(cls) -> "ListingRepository":
        repo = cls()
        # marketplace samples first so they lead the grid (ids 9-15)
        for i, (title, category, price, unit, deliverable) in enumerate(_MARKET_SAMPLES, start=9):
            repo.save(Listing(
                id=i, owner_email=SAMPLE_SELLER_EMAIL, title=title, price=price,
                category=category, deliverable=deliverable, unit=unit,
                description=_MARKET_DESCRIPTION,
            ))
        for i, (title, price, category, deliverable, unit, desc) in enumerate(_DEMO_SAMPLES, start=1):
            repo.save(Listing(
                id=i, owner_email=DEMO_EMAIL, title=title, price=price,
                category=category, deliverable=deliverable, unit=unit, description=desc,
            ))
        return repo
