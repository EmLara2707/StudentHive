"""Authentication use-cases. Knows nothing about Streamlit or session_state:
it takes plain values in and returns an AuthResult for the view to act on."""
from dataclasses import dataclass

from models.user import User
from repositories.user_repository import UserRepository
from utils.security import hash_password, verify_password


@dataclass(frozen=True)
class AuthResult:
    ok: bool
    user: User | None = None
    error: str | None = None

    @classmethod
    def success(cls, user: User) -> "AuthResult":
        return cls(ok=True, user=user)

    @classmethod
    def failure(cls, message: str) -> "AuthResult":
        return cls(ok=False, error=message)


class AuthController:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def login(self, email: str, password: str) -> AuthResult:
        email = (email or "").strip()
        if not email or not password:
            return AuthResult.failure("Please fill in all fields.")

        user = self._users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            return AuthResult.failure("Invalid email or password.")
        return AuthResult.success(user)

    def register(self, full_name: str, email: str, password: str,
                 confirm_password: str) -> AuthResult:
        full_name = (full_name or "").strip()
        email = (email or "").strip()
        if not full_name or not email or not password or not confirm_password:
            return AuthResult.failure("Please fill in all fields.")
        if password != confirm_password:
            return AuthResult.failure("Passwords do not match.")
        if self._users.exists(email):
            return AuthResult.failure("An account with this email already exists.")

        user = User(name=full_name, email=email,
                    password_hash=hash_password(password), onboarded=False)
        self._users.add(user)
        return AuthResult.success(user)
