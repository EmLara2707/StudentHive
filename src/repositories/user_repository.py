"""In-memory user storage. Swap this class for a DB-backed one later;
controllers only depend on these method names."""
import secrets

from models.profile import Profile
from models.user import User
from repositories.seed_data import SAMPLE_STUDENTS
from utils.images import to_data_uri
from utils.security import hash_password

DEMO_EMAIL = "demo@mmcm.edu.ph"
# Sample seller that owns the seeded marketplace listings. Nobody can log in as
# this account (its password is random), it only exists so listings have an owner.
SAMPLE_SELLER_EMAIL = "ana.r@mmcm.edu.ph"


class UserRepository:
    def __init__(self) -> None:
        self._users: dict[str, User] = {}

    @staticmethod
    def _key(email: str) -> str:
        return email.strip().lower()

    def get_by_email(self, email: str) -> User | None:
        return self._users.get(self._key(email))

    def get_many(self, emails) -> "dict[str, User]":
        """Several users in one call: {lower-cased email: User}. Emails that match
        nobody are simply missing from the result. Callers look up with
        email.strip().lower()."""
        found: dict[str, User] = {}
        for email in emails:
            key = self._key(email)
            user = self._users.get(key)
            if user is not None:
                found[key] = user
        return found

    def exists(self, email: str) -> bool:
        return self._key(email) in self._users

    def add(self, user: User) -> None:
        key = self._key(user.email)
        if key in self._users:
            raise ValueError("User already exists")
        user.email = key
        self._users[key] = user

    def save(self, user: User) -> None:
        """Persist changes to an existing user (a DB repo would UPDATE here)."""
        self._users[self._key(user.email)] = user

    def set_photo(self, email: str, data: bytes, mime: str) -> bool:
        """Store a profile photo. In memory the "URL" is a data: URI; the Supabase
        repository uploads to Storage and keeps a public URL instead."""
        user = self._users.get(self._key(email))
        if user is None:
            return False
        user.profile.photo_url = to_data_uri(data, mime)
        user.profile.photo_mime = mime
        return True

    def delete(self, email: str) -> bool:
        return self._users.pop(self._key(email), None) is not None

    @classmethod
    def seeded(cls) -> "UserRepository":
        """Demo account (already onboarded) plus the sample students."""
        repo = cls()
        repo.add(User(
            name="Demo Student",
            email=DEMO_EMAIL,
            password_hash=hash_password("demo1234"),
            onboarded=True,
            profile=Profile(
                major="Bachelor of Computer Science",
                bio=("Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 6).strip(),
                skills=["Figma", "Python", "Tutoring"],
                socials=["stdnt@hive.com"],
            ),
        ))
        # nobody can log in as a sample student: one random, discarded password for all
        unusable_hash = hash_password(secrets.token_hex(16))
        for s in SAMPLE_STUDENTS:
            repo.add(User(
                name=s.name,
                email=s.email,
                password_hash=unusable_hash,
                onboarded=True,
                profile=Profile(
                    major=s.major, bio=s.bio, skills=list(s.skills), socials=s.socials,
                ),
            ))
        return repo
