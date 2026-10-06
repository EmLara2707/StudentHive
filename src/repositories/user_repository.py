"""In-memory user storage. Swap this class for a DB-backed one later;
controllers only depend on these method names."""
from models.user import User
from utils.security import hash_password


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

    @classmethod
    def seeded(cls) -> "UserRepository":
        """Repository with one demo account (already onboarded) for testing."""
        repo = cls()
        repo.add(User(
            name="Demo Student",
            email="admin",
            password_hash=hash_password("admin"),
            onboarded=True,
        ))
        return repo
