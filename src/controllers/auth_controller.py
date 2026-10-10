"""Authentication use-cases. Knows nothing about Streamlit or session_state:
it takes plain values in and returns an AuthResult for the view to act on."""
import re
from dataclasses import dataclass

from models.user import User
from repositories import auth_gateway as gw
from repositories.errors import RepositoryError
from repositories.listing_repository import ListingRepository
from repositories.review_repository import ReviewRepository
from repositories.transaction_repository import TransactionRepository
from repositories.user_repository import UserRepository

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# StudentHive is for verified students: only addresses on these domains (or their
# subdomains, e.g. student.ateneo.edu.ph) can register. Use ("mmcm.edu.ph",) for MMCM only.
SCHOOL_EMAIL_DOMAINS = ("mcm.edu.ph",)


@dataclass(frozen=True)
class AuthResult:
    ok: bool
    user: User | None = None
    error: str | None = None
    # Added for Supabase Auth (the three fields above are unchanged):
    needs_confirmation: bool = False        # signed up, but must click the email link first
    tokens: tuple[str, str] | None = None   # (access, refresh) for the view to remember
    # A6: True when a failure was only a network problem, so the saved login is still good.
    can_retry: bool = False

    @classmethod
    def success(cls, user: User | None = None, tokens: tuple[str, str] | None = None,
                needs_confirmation: bool = False) -> "AuthResult":
        return cls(ok=True, user=user, tokens=tokens, needs_confirmation=needs_confirmation)

    @classmethod
    def failure(cls, message: str, can_retry: bool = False) -> "AuthResult":
        return cls(ok=False, error=message, can_retry=can_retry)


class AuthController:
    MIN_PASSWORD_LENGTH = 8
    DELETE_CONFIRMATION = "DELETE"

    def __init__(self, users: UserRepository, listings: ListingRepository,
                 reviews: ReviewRepository, transactions: TransactionRepository,
                 gateway=None) -> None:
        self._users = users
        self._listings = listings
        self._reviews = reviews
        self._transactions = transactions
        # SupabaseAuthGateway or InMemoryAuthGateway. views/session.py passes it; when it
        # doesn't, fall back to the in-memory one so the app works either way.
        self._gateway = gateway if gateway is not None else gw.InMemoryAuthGateway(users)

    @staticmethod
    def _message_for(outcome) -> str:
        """Student-facing text for a failed gateway call. The existing messages are
        kept word for word; only the Supabase-only states are new."""
        code = outcome.error_code
        if code == gw.INVALID_CREDENTIALS:
            return "Invalid email or password."
        if code == gw.EMAIL_NOT_CONFIRMED:
            return "Please confirm your email first. Check your inbox for the link."
        if code == gw.ALREADY_REGISTERED:
            return "An account with this email already exists."
        if code == gw.WEAK_PASSWORD:
            return "That password is too weak. Try a longer one."
        if code == gw.RATE_LIMITED:
            return "Too many attempts. Please wait a moment and try again."
        if code == gw.SIGNUP_REJECTED:
            return "Please use your school email address (it ends in .edu.ph)."
        return RepositoryError.DEFAULT_MESSAGE

    def login(self, email: str, password: str) -> AuthResult:
        email = (email or "").strip()
        if not email or not password:
            return AuthResult.failure("Please fill in all fields.")

        outcome = self._gateway.sign_in(email, password)
        if not outcome.ok:
            return AuthResult.failure(self._message_for(outcome))
        user = self._users.get_by_email(email)
        if user is None:        # signed in, but no profile row: treat as a failed login
            return AuthResult.failure("Invalid email or password.")
        return AuthResult.success(user, tokens=outcome.tokens)

    # ---- A6: keeping a person signed in across browser refreshes ----
    _EXPIRED = "Your session expired. Please log in again."

    @property
    def remembers_logins(self) -> bool:
        """True with Supabase Auth (a cookie can bring the login back); False for the
        in-memory fallback, where there is nothing to restore."""
        return getattr(self._gateway, "in_memory", True) is False

    def _exchange(self, tokens):
        """One refresh-token exchange. Returns (outcome, failed AuthResult or None)."""
        outcome = self._gateway.restore_session(tokens)
        if outcome.ok and outcome.tokens:
            return outcome, None
        return outcome, AuthResult.failure(
            self._EXPIRED, can_retry=outcome.error_code == gw.NETWORK)

    def renew_tokens(self, tokens) -> AuthResult:
        """Exchange the refresh token (or an (access, refresh) pair) for a NEW pair.
        Supabase refresh tokens are single-use, so the caller must store the new pair."""
        outcome, failed = self._exchange(tokens)
        return failed or AuthResult.success(tokens=outcome.tokens)

    def restore(self, refresh_token: str) -> AuthResult:
        """Sign someone back in from the refresh token in their cookie: renew the tokens,
        then load their profile. On success `tokens` holds the NEW pair to remember."""
        outcome, failed = self._exchange(refresh_token)
        if failed:
            return failed
        try:
            user = self._users.get_by_email(outcome.email) if outcome.email else None
        except RepositoryError:     # tokens were renewed but the profile couldn't be read
            return AuthResult.failure(self._EXPIRED)   # the old token is spent: log in again
        if user is None:        # valid login but no profile row: same as an expired one
            return AuthResult.failure(self._EXPIRED)
        return AuthResult.success(user, tokens=outcome.tokens)

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

        outcome = self._gateway.sign_up(full_name, email, password)
        if not outcome.ok:
            return AuthResult.failure(self._message_for(outcome))
        if outcome.needs_confirmation:      # Supabase: not signed in until the email link
            return AuthResult.success(needs_confirmation=True)
        user = self._users.get_by_email(email)
        return AuthResult.success(user, tokens=outcome.tokens)

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
        # Check the current password by signing in again with it.
        outcome = self._gateway.sign_in(email, current)
        if not outcome.ok:
            if outcome.error_code == gw.INVALID_CREDENTIALS:
                return "Current password is incorrect."
            return self._message_for(outcome)
        return None

    def change_password(self, email: str, current: str, new: str,
                        verify: str) -> AuthResult:
        error = self.validate_password_change(email, current, new, verify)
        if error:
            return AuthResult.failure(error)
        outcome = self._gateway.update_password(new)
        if not outcome.ok:
            return AuthResult.failure(self._message_for(outcome))
        return AuthResult.success(self._users.get_by_email(email))

    # ---- account deletion ----
    def delete_account(self, email: str, confirmation: str) -> AuthResult:
        if (confirmation or "").strip() != self.DELETE_CONFIRMATION:
            return AuthResult.failure(f"Type {self.DELETE_CONFIRMATION} to confirm.")
        if self._users.get_by_email(email) is None:
            return AuthResult.failure("Account not found.")
        # The gateway deletes the account: in memory it removes the user, on Supabase it
        # deletes the auth user and the foreign keys cascade to everything below it.
        # Supabase side: only the signed-in person's own id is ever used.
        user_id = self._gateway.current_user_id() or email
        if "@" in user_id and user_id.lower() != email.strip().lower():
            return AuthResult.failure("Account not found.")   # signed in as someone else
        if not self._gateway.admin_delete_user(user_id).ok:
            return AuthResult.failure("Account not found.")
        # Cascade by email: nothing may be left behind for the next person who registers
        # this email: its listings, its transactions (on both sides), the reviews written
        # about it and the reviews it wrote. Kept until Person B's repositories are
        # merged (A8 removes it). On Supabase the account is already gone and the
        # database cascaded, so a failure here must not report the deletion as failed.
        try:
            self._listings.delete_by_owner(email)
            self._transactions.delete_for_user(email)
            self._reviews.delete_for_user(email)
            self._reviews.delete_by_reviewer(email)
        except RepositoryError:
            pass
        return AuthResult.success()
