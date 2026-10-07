"""In-memory user storage. Swap this class for a DB-backed one later;
controllers only depend on these method names."""
from models.profile import Profile
from models.user import User
from utils.security import hash_password

DEMO_EMAIL = "demo@mmcm.edu.ph"


class UserRepository:
    def __init__(self) -> None:
        self._users: dict[str, User] = {}

    @staticmethod
    def _key(email: str) -> str:
        return email.strip().lower()

    def get_by_email(self, email: str) -> User | None:
        return self._users.get(self._key(email))

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

    def delete(self, email: str) -> bool:
        return self._users.pop(self._key(email), None) is not None

    @classmethod
    def seeded(cls) -> "UserRepository":
        """Repository with one demo account (already onboarded, sample profile)."""
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
        return repo
