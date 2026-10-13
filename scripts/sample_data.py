"""DEV / STAGING sample data for scripts/seed_users.py and scripts/seed_market.py.

The app itself holds no sample data any more: everything it shows comes from Supabase.
This module only builds plain model objects (users, listings, transactions, reviews) that
the two seed scripts write into a development project. It is NOT imported by src/."""
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))   # models, utils

from models.listing import GIG, RENTAL, Listing                       # noqa: E402
from models.profile import Profile                                    # noqa: E402
from models.review import Review                                      # noqa: E402
from models.transaction import (                                      # noqa: E402
    PLACEHOLDER_IMAGE, Transaction, TransactionKind, TransactionStatus,
)
from models.user import User                                          # noqa: E402
from utils.clock import today_manila                                  # noqa: E402

DEMO_EMAIL = "demo@mcm.edu.ph"
# The sample student who owns the marketplace listings. Nobody can sign in as this account.
SAMPLE_SELLER_EMAIL = "ana.r@mcm.edu.ph"


def email_for(name: str) -> str:
    """'Ana R.' -> 'ana.r@mcm.edu.ph'"""
    slug = name.strip().lower().rstrip(".").replace(" ", ".")
    return f"{slug}@mcm.edu.ph"


@dataclass(frozen=True)
class SampleStudent:
    name: str
    major: str
    skills: tuple[str, ...]
    rating: float                      # average of the two sample reviews
    listings: tuple[tuple[str, int], ...] = ()   # (title, price per day)

    @property
    def email(self) -> str:
        return email_for(self.name)

    @property
    def bio(self) -> str:
        topics = ", ".join(self.skills[:2]).lower() if self.skills else "all kinds of gigs"
        return (f"Hi, I'm {self.name}! I'm a student who enjoys helping others with "
                f"{topics}. Message me anytime if you'd like to work together.")

    @property
    def socials(self) -> list[str]:
        return [f"{self.name.split()[0].lower()}@hive.com"]

    @property
    def review_ratings(self) -> tuple[float, float]:
        """Two ratings whose average is `rating` (the first is always 5.0)."""
        return 5.0, round(2 * self.rating - 5.0, 1)


# Ana R.'s listings are the marketplace samples (see sample_listings below).
SAMPLE_STUDENTS = (
    SampleStudent("Ana R.", "Bachelor of Mathematics", ("Calculus", "Statistics", "Tutoring"), 4.9),
    SampleStudent("Miguel S.", "Bachelor of Fine Arts", ("Photography", "Lightroom", "Videography"), 4.8,
                  (("Event Photography", 1200),)),
    SampleStudent("Carla D.", "Bachelor of Design", ("Figma", "Illustrator", "Branding"), 4.7,
                  (("Poster Design", 400),)),
    SampleStudent("Dan K.", "Bachelor of English", ("Proofreading", "Academic Writing"), 4.6,
                  (("Thesis Proofreading", 300),)),
    SampleStudent("Nina T.", "Bachelor of Veterinary Science", ("Pet Care", "Dog Training"), 4.9,
                  (("Dog Walking", 250),)),
    SampleStudent("Josh P.", "Bachelor of Music", ("Guitar", "Music Theory"), 4.8,
                  (("Guitar Lessons", 350),)),
    SampleStudent("Sam W.", "Bachelor of Business", ("Resumes", "Career Coaching"), 4.5,
                  (("Resume Review", 400),)),
    SampleStudent("Leo M.", "Bachelor of Computer Science", ("Python", "Data Structures", "Tutoring"), 4.7,
                  (("Python Tutoring", 450),)),
    SampleStudent("Rico B.", "Bachelor of Media Arts", ("Video Editing", "Premiere Pro"), 4.8,
                  (("Video Editing", 800),)),
    SampleStudent("Mia L.", "Bachelor of Graphic Design", ("Logo Design", "Illustrator"), 4.9,
                  (("Logo Design", 600),)),
    SampleStudent("Paolo G.", "Bachelor of Film", ("Videography", "Color Grading"), 4.6,
                  (("Wedding Videography", 1500),)),
    SampleStudent("Kyla V.", "Bachelor of Marketing", ("Social Media", "Copywriting"), 4.7,
                  (("Social Media Management", 350),)),
)

SAMPLE_REVIEWS = (
    ("Student A", "Clear communication and always on time."),
    ("Student B", "Great work, would happily hire again."),
)


# ------------------------------------------------------------ users
def sample_users() -> list[User]:
    """The demo account (already onboarded) first, then the 12 sample students."""
    users = [User(
        name="Demo Student",
        email=DEMO_EMAIL,
        onboarded=True,
        profile=Profile(
            major="Bachelor of Computer Science",
            bio=("Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 6).strip(),
            skills=["Figma", "Python", "Tutoring"],
            socials=["stdnt@hive.com"],
        ),
    )]
    for s in SAMPLE_STUDENTS:
        users.append(User(
            name=s.name, email=s.email, onboarded=True,
            profile=Profile(major=s.major, bio=s.bio, skills=list(s.skills), socials=s.socials),
        ))
    return users


# ------------------------------------------------------------ listings
SERVICE, PROJECT = "Service Deliverables", "Project Deliverables"

# Demo user's own listings: (title, price, category, deliverable, unit, description)
_DEMO_LISTINGS = [
    ("Python Tutoring", 20, GIG, SERVICE, "hr", "One-on-one Python tutoring for beginners."),
    ("Figma Design Review", 25, GIG, SERVICE, "hr", "Feedback on your Figma layouts and prototypes."),
    ("Calculus Help", 18, GIG, SERVICE, "hr", "Help with limits, derivatives and integrals."),
    ("Resume Workshop", 15, GIG, SERVICE, "hr", "Polish your resume and cover letter."),
    ("Guitar Lessons", 30, GIG, SERVICE, "hr", "Acoustic guitar lessons for all levels."),
    ("Essay Proofreading", 12, GIG, PROJECT, "once", "Grammar and clarity pass on your essay."),
    ("Camera Rental", 40, RENTAL, "", "day", "DSLR camera with a kit lens and bag."),
    ("Spanish Conversation", 22, GIG, SERVICE, "hr", "Practice conversational Spanish."),
]

# Marketplace listings from the sample seller: (title, category, price, unit, deliverable)
_MARKET_LISTINGS = [
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


def sample_listings() -> list[Listing]:
    """Newest first: the marketplace samples lead, then the demo user's own."""
    listings = [
        Listing(id=i, owner_email=SAMPLE_SELLER_EMAIL, title=title, price=price,
                category=category, deliverable=deliverable, unit=unit,
                description=_MARKET_DESCRIPTION)
        for i, (title, category, price, unit, deliverable) in enumerate(_MARKET_LISTINGS, start=9)
    ]
    listings += [
        Listing(id=i, owner_email=DEMO_EMAIL, title=title, price=price,
                category=category, deliverable=deliverable, unit=unit, description=desc)
        for i, (title, price, category, deliverable, unit, desc) in enumerate(_DEMO_LISTINGS, start=1)
    ]
    return listings


# ------------------------------------------------------------ transactions
G, R = TransactionKind.GIG, TransactionKind.RENTAL
ACTIVE, PENDING = TransactionStatus.ACTIVE, TransactionStatus.PENDING
COMPLETED, CANCELLED = TransactionStatus.COMPLETED, TransactionStatus.CANCELLED

# (kind, item, demo user is the provider?, status, cancelled by "me"/"them"/None,
#  start offset, end offset (days from today), price per day, other student)
_TRANSACTIONS = [
    # ---- Gigs ----
    (G, "Math Tutoring (Calculus)",  True,  ACTIVE,    None,   -3,  -1,  500, "Ana R."),
    (G, "Event Photography",         True,  ACTIVE,    None,    1,   4, 1200, "Miguel S."),
    (G, "Poster Design",             False, ACTIVE,    None,    0,   2,  400, "Carla D."),
    (G, "Thesis Proofreading",       False, ACTIVE,    None,    2,   3,  300, "Dan K."),
    (G, "Dog Walking",               True,  ACTIVE,    None,   12,  15,  250, "Nina T."),
    (G, "Guitar Lessons",            True,  PENDING,   None,    5,   7,  350, "Josh P."),
    (G, "Resume Review",             True,  PENDING,   None,    3,   4,  400, "Sam W."),
    (G, "Python Tutoring",           False, PENDING,   None,    9,  10,  450, "Leo M."),
    (G, "Video Editing",             True,  COMPLETED, None,  -20, -18,  800, "Rico B."),
    (G, "Logo Design",               False, COMPLETED, None,  -14, -11,  600, "Mia L."),
    (G, "Essay Editing",             True,  COMPLETED, None,   -9,  -8,  200, "Ana R."),
    (G, "Wedding Videography",       True,  CANCELLED, "me",   -6,  -5, 1500, "Paolo G."),
    (G, "Social Media Management",   False, CANCELLED, "them", -2,  -1,  350, "Kyla V."),
    # ---- Rentals ----
    (R, "Canon DSLR Camera",         False, ACTIVE,    None,   -3,  -1,  500, "Ana R."),
    (R, "Camping Tent (4P)",         False, ACTIVE,    None,    1,   4,  350, "Miguel S."),
    (R, "Projector",                 True,  ACTIVE,    None,    0,   2,  400, "Carla D."),
    (R, "Portable Speaker",          True,  ACTIVE,    None,    2,   3,  180, "Dan K."),
    (R, "Folding Bike",              True,  ACTIVE,    None,   12,  15,  250, "Nina T."),
    (R, "Electric Guitar",           True,  PENDING,   None,    5,   7,  300, "Josh P."),
    (R, "Gaming Console",            True,  PENDING,   None,    3,   4,  350, "Sam W."),
    (R, "Power Drill",               False, PENDING,   None,    9,  10,  150, "Leo M."),
    (R, "Karaoke Set",               False, COMPLETED, None,  -20, -18,  600, "Rico B."),
    (R, "Acoustic Guitar",           True,  COMPLETED, None,  -14, -11,  200, "Mia L."),
    (R, "Tripod Stand",              False, COMPLETED, None,   -9,  -8,  100, "Ana R."),
    (R, "Sound System",              False, CANCELLED, "me",   -6,  -5,  800, "Paolo G."),
    (R, "Ring Light",                True,  CANCELLED, "them", -2,  -1,  120, "Kyla V."),
]


def sample_transactions(today: date | None = None) -> list[Transaction]:
    """Sample history between the demo user and the sample students, dated relative to today."""
    today = today or today_manila()
    out = []
    for n, (kind, item, is_provider, status, cancelled, a, b, price, other) in enumerate(_TRANSACTIONS, start=1):
        other_email = email_for(other)
        provider, requester = ((DEMO_EMAIL, other_email) if is_provider
                               else (other_email, DEMO_EMAIL))
        start, end = today + timedelta(days=a), today + timedelta(days=b)
        quantity = (end - start).days + 1
        cancelled_by = {"me": DEMO_EMAIL, "them": other_email}.get(cancelled)
        out.append(Transaction(
            id=n, kind=kind, item=item, image=PLACEHOLDER_IMAGE,
            provider_email=provider, requester_email=requester,
            start=start, end=end, price=price, unit="day",
            quantity=quantity, total=price * quantity,
            status=status, cancelled_by=cancelled_by,
        ))
    return out


# ------------------------------------------------------------ reviews
def sample_reviews() -> list[Review]:
    """Two reviews for the demo user, then two for each sample student."""
    reviews = [
        Review("Student A", DEMO_EMAIL, 5.0, "Clear explanations and always on time."),
        Review("Student B", DEMO_EMAIL, 5.0, "Helped me finally understand recursion."),
    ]
    for s in SAMPLE_STUDENTS:
        for (reviewer, text), rating in zip(SAMPLE_REVIEWS, s.review_ratings):
            reviews.append(Review(reviewer, s.email, rating, text))
    return reviews
