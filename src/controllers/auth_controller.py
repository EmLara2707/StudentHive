"""Authentication use-cases. Knows nothing about Streamlit or session_state:
it takes plain values in and returns an AuthResult for the view to act on."""
import re
from dataclasses import dataclass

from models.user import User
from repositories.listing_repository import ListingRepository
from repositories.review_repository import ReviewRepository
from repositories.transaction_repository import TransactionRepository
from repositories.user_repository import UserRepository
from utils.security import hash_password, verify_password

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# StudentHive is for verified students: only addresses on these domains (or their
# subdomains, e.g. student.ateneo.edu.ph) can register. Use ("mmcm.edu.ph",) for MMCM only.
SCHOOL_EMAIL_DOMAINS = ("edu.ph",)


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
                 reviews: ReviewRepository, transactions: TransactionRepository) -> None:
        self._users = users
        self._listings = listings
        self._reviews = reviews
        self._transactions = transactions

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
        if not _EMAIL_PATTERN.match(email):
            return AuthResult.failure("Please enter a valid email address.")
        if not self.is_school_email(email):
            return AuthResult.failure("Please use your school email address (it ends in .edu.ph).")
        if len(password) < self.MIN_PASSWORD_LENGTH:
            return AuthResult.failure(
                f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters.")
        if password != confirm_password:
            return AuthResult.failure("Passwords do not match.")
        if self._users.exists(email):
            return AuthResult.failure("An account with this email already exists.")

        user = User(name=full_name, email=email,
                    password_hash=hash_password(password), onboarded=False)
        self._users.add(user)
        return AuthResult.success(user)

    @staticmethod
    def is_school_email(email: str) -> bool:
        domain = email.strip().lower().rsplit("@", 1)[-1]
        return any(domain == d or domain.endswith("." + d) for d in SCHOOL_EMAIL_DOMAINS)

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
        # Cascade: nothing may be left behind for the next person who registers this
        # email: its listings, its transactions (on both sides), the reviews written
        # about it and the reviews it wrote.
        self._listings.delete_by_owner(email)
        self._transactions.delete_for_user(email)
        self._reviews.delete_for_user(email)
        self._reviews.delete_by_reviewer(email)
        return AuthResult.success()
