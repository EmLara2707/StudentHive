"""Demo students used to seed the in-memory repositories. Not used in production:
a real database replaces this file. No Streamlit, no storage logic."""
from dataclasses import dataclass


def email_for(name: str) -> str:
    """'Ana R.' -> 'ana.r@mmcm.edu.ph'"""
    slug = name.strip().lower().rstrip(".").replace(" ", ".")
    return f"{slug}@mmcm.edu.ph"


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


# Ana R.'s listings are the seeded marketplace samples in listing_repository.
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
