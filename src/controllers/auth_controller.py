"""Authentication use-cases. Knows nothing about Streamlit or session_state:
it takes plain values in and returns an AuthResult for the view to act on."""
from dataclasses import dataclass

from models.user import User
from repositories.listing_repository import ListingRepository
from repositories.review_repository import ReviewRepository
from repositories.user_repository import UserRepository
from utils.security import hash_password, verify_password


@dataclass(frozen=True)
class AuthResult:
    ok: bool
    user: User | None = None
    error: str | None = None

    @classmethod
    def success(cls, user: User | None = None) -> "AuthResult":
        return cls(ok=True, user=user)

    @classmethod
    def failure(cls, message: str) -> "AuthResult":
        return cls(ok=False, error=message)


class AuthController:
    MIN_PASSWORD_LENGTH = 8
    DELETE_CONFIRMATION = "DELETE"

    def __init__(self, users: UserRepository, listings: ListingRepository,
                 reviews: ReviewRepository) -> None:
        self._users = users
        self._listings = listings
        self._reviews = reviews

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

    # ---- password change ----
    def validate_password_change(self, email: str, current: str, new: str,
                                 verify: str) -> str | None:
        """Return an error message, or None if the change is allowed."""
        if not (current and new and verify):
            return "Fill in all three password fields."
        if len(new) < self.MIN_PASSWORD_LENGTH:
            return f"New password must be at least {self.MIN_PASSWORD_LENGTH} characters."
        if new != verify:
            return "New passwords don’t match."
        if new == current:
            return "New password must be different from your current one."
        user = self._users.get_by_email(email)
        if user is None or not verify_password(current, user.password_hash):
            return "Current password is incorrect."
        return None

    def change_password(self, email: str, current: str, new: str,
                        verify: str) -> AuthResult:
        error = self.validate_password_change(email, current, new, verify)
        if error:
            return AuthResult.failure(error)
        user = self._users.get_by_email(email)
        user.password_hash = hash_password(new)
        self._users.save(user)
        return AuthResult.success(user)

    # ---- account deletion ----
    def delete_account(self, email: str, confirmation: str) -> AuthResult:
        if (confirmation or "").strip() != self.DELETE_CONFIRMATION:
            return AuthResult.failure(f"Type {self.DELETE_CONFIRMATION} to confirm.")
        if not self._users.delete(email):
            return AuthResult.failure("Account not found.")
        # Cascade: the account's listings and the reviews written about it go too.
        self._listings.delete_by_owner(email)
        self._reviews.delete_for_user(email)
        return AuthResult.success()
