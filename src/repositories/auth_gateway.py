"""A2: the auth gateway. The ONLY place that talks to Supabase Auth.

AuthController (A3) calls this instead of checking password hashes itself. Rules:
  * No Streamlit import (layer rule).
  * Every method returns an AuthOutcome. It never raises a raw Supabase exception:
    failures come back as outcome.ok == False with a short machine-readable
    error_code, so the controller decides which student-facing message to show.
  * It holds the per-session client it is given; it never builds or caches one.
  * The admin client is only reached through the get_admin_client function, and only
    by admin_delete_user.
"""
from __future__ import annotations

from dataclasses import dataclass

from models.user import User
from utils.security import hash_password, verify_password

# error_code values the controller can switch on
INVALID_CREDENTIALS = "invalid_credentials"   # wrong email or password
EMAIL_NOT_CONFIRMED = "email_not_confirmed"   # signed up, link in the inbox not clicked yet
ALREADY_REGISTERED = "already_registered"
WEAK_PASSWORD = "weak_password"
SIGNUP_REJECTED = "signup_rejected"           # trigger or provider refused the signup
RATE_LIMITED = "rate_limited"
SESSION_EXPIRED = "session_expired"           # refresh token no longer valid
NETWORK = "network"
NOT_CONFIGURED = "not_configured"             # e.g. no service key for admin_delete_user
UNKNOWN = "unknown"


@dataclass(frozen=True)
class AuthOutcome:
    """Plain result of one auth call. Tokens are only set when a session exists."""
    ok: bool
    user_id: str | None = None
    email: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    needs_confirmation: bool = False      # sign_up worked but the user must confirm by email
    error_code: str | None = None
    message: str | None = None            # developer-facing detail, not for students

    @property
    def tokens(self) -> tuple[str, str] | None:
        if self.access_token and self.refresh_token:
            return (self.access_token, self.refresh_token)
        return None

    @classmethod
    def failure(cls, code: str, message: str | None = None) -> "AuthOutcome":
        return cls(ok=False, error_code=code, message=message)


def _outcome_from_response(response, *, needs_confirmation: bool = False) -> AuthOutcome:
    """Turn a supabase AuthResponse into an AuthOutcome."""
    user = getattr(response, "user", None)
    session = getattr(response, "session", None)
    return AuthOutcome(
        ok=True,
        user_id=str(user.id) if user is not None else None,
        email=(user.email or "").lower() if user is not None else None,
        access_token=session.access_token if session is not None else None,
        refresh_token=session.refresh_token if session is not None else None,
        needs_confirmation=needs_confirmation,
    )


def _classify(exc: Exception) -> AuthOutcome:
    """Map any exception from the Supabase library to a failure outcome."""
    # Imported here so this module can be imported (and tested) without the library
    # doing any work, and so a library layout change breaks one function, not the file.
    from supabase import AuthApiError, AuthError, AuthWeakPasswordError

    text = str(exc)
    if isinstance(exc, AuthWeakPasswordError):
        return AuthOutcome.failure(WEAK_PASSWORD, text)
    if isinstance(exc, AuthApiError):
        code = (getattr(exc, "code", None) or "").lower()
        status = getattr(exc, "status", None)
        if code == "email_not_confirmed":
            return AuthOutcome.failure(EMAIL_NOT_CONFIRMED, text)
        if code in ("invalid_credentials", "invalid_login_credentials"):
            return AuthOutcome.failure(INVALID_CREDENTIALS, text)
        if code in ("user_already_exists", "email_exists"):
            return AuthOutcome.failure(ALREADY_REGISTERED, text)
        if code == "weak_password":
            return AuthOutcome.failure(WEAK_PASSWORD, text)
        if code in ("over_request_rate_limit", "over_email_send_rate_limit") or status == 429:
            return AuthOutcome.failure(RATE_LIMITED, text)
        if code in ("refresh_token_not_found", "refresh_token_already_used",
                    "session_not_found", "session_expired", "bad_jwt"):
            return AuthOutcome.failure(SESSION_EXPIRED, text)
        # Older servers send no code: fall back to the message text.
        lowered = text.lower()
        if "invalid login credentials" in lowered:
            return AuthOutcome.failure(INVALID_CREDENTIALS, text)
        if "email not confirmed" in lowered:
            return AuthOutcome.failure(EMAIL_NOT_CONFIRMED, text)
        if "already registered" in lowered:
            return AuthOutcome.failure(ALREADY_REGISTERED, text)
        if "database error saving new user" in lowered:
            return AuthOutcome.failure(SIGNUP_REJECTED, text)
        if "refresh token" in lowered:
            return AuthOutcome.failure(SESSION_EXPIRED, text)
        return AuthOutcome.failure(UNKNOWN, text)
    if isinstance(exc, AuthError):
        # AuthSessionMissingError and friends: there is no (valid) session
        lowered = text.lower()
        if "session" in lowered or "token" in lowered:
            return AuthOutcome.failure(SESSION_EXPIRED, text)
        return AuthOutcome.failure(UNKNOWN, text)
    # Anything else (httpx timeouts, DNS, connection refused...) is a network problem.
    return AuthOutcome.failure(NETWORK, f"{type(exc).__name__}: {text}")


class SupabaseAuthGateway:
    """Supabase Auth behind plain method calls.

    client           this browser session's client (carries the user's token)
    get_admin_client a FUNCTION returning the service-role client or None, so the
                     service key is only touched when an account is really deleted
    """

    # views/session.py drops anything with in_memory = False on logout: this gateway is
    # tied to one person's client (same convention as the Supabase repositories).
    in_memory = False

    def __init__(self, client, get_admin_client) -> None:
        self._client = client
        self._get_admin_client = get_admin_client

    def current_user_id(self) -> str | None:
        """The signed-in user's Supabase id, read from this session's client, or None.
        AuthController.delete_account uses it, so an account can only be deleted by the
        person who is signed in to it."""
        try:
            session = self._client.auth.get_session()
            return str(session.user.id) if session is not None and session.user else None
        except Exception:
            return None

    # ---- sign up / sign in / sign out ----
    def sign_up(self, name: str, email: str, password: str) -> AuthOutcome:
        """Create the account. The signup trigger reads options.data.name to fill
        profiles.name, so the name must travel as user metadata.

        With email confirmation ON (the decided setup) there is no session yet:
        the outcome has needs_confirmation=True and no tokens."""
        try:
            response = self._client.auth.sign_up({
                "email": email.strip().lower(),
                "password": password,
                "options": {"data": {"name": name.strip()}},
            })
        except Exception as exc:
            return _classify(exc)

        user = getattr(response, "user", None)
        if user is None:
            return AuthOutcome.failure(UNKNOWN, "sign_up returned no user")
        # Supabase hides "already registered" when confirmation is on: it returns a
        # fake user with an EMPTY identities list instead of an error.
        identities = getattr(user, "identities", None)
        if identities is not None and len(identities) == 0:
            return AuthOutcome.failure(ALREADY_REGISTERED, "email already registered")
        session = getattr(response, "session", None)
        return _outcome_from_response(response, needs_confirmation=session is None)

    def sign_in(self, email: str, password: str) -> AuthOutcome:
        """Email + password. On success the client now carries the user's token and
        the outcome holds the tokens for the app to remember."""
        try:
            response = self._client.auth.sign_in_with_password({
                "email": email.strip().lower(),
                "password": password,
            })
        except Exception as exc:
            return _classify(exc)
        if getattr(response, "session", None) is None:
            return AuthOutcome.failure(UNKNOWN, "sign_in returned no session")
        return _outcome_from_response(response)

    def sign_out(self) -> AuthOutcome:
        """End THIS session only (scope local), not the user's other devices."""
        try:
            self._client.auth.sign_out({"scope": "local"})
        except Exception as exc:
            return _classify(exc)
        return AuthOutcome(ok=True)

    # ---- password ----
    def update_password(self, new_password: str) -> AuthOutcome:
        """Change the signed-in user's password. The controller verifies the current
        password first by calling sign_in again."""
        try:
            response = self._client.auth.update_user({"password": new_password})
        except Exception as exc:
            return _classify(exc)
        user = getattr(response, "user", None)
        return AuthOutcome(
            ok=True,
            user_id=str(user.id) if user is not None else None,
            email=(user.email or "").lower() if user is not None else None,
        )

    # ---- session restore (after a browser refresh) ----
    def restore_session(self, tokens) -> AuthOutcome:
        """Turn remembered tokens back into a live session.

        `tokens` is (access_token, refresh_token) or just the refresh token string
        (what the cookie holds). Supabase refresh tokens are single-use: this
        ALWAYS exchanges the refresh token and returns the NEW pair in the outcome.
        The caller must store that new pair (session_state and the cookie) or the
        next restore will fail."""
        refresh_token = tokens[1] if isinstance(tokens, (tuple, list)) else tokens
        if not refresh_token:
            return AuthOutcome.failure(SESSION_EXPIRED, "no refresh token")
        try:
            response = self._client.auth.refresh_session(refresh_token)
        except Exception as exc:
            return _classify(exc)
        if getattr(response, "session", None) is None:
            return AuthOutcome.failure(SESSION_EXPIRED, "refresh returned no session")
        return _outcome_from_response(response)

    # ---- account deletion (admin only) ----
    def admin_delete_user(self, user_id: str) -> AuthOutcome:
        """Delete the auth user. Foreign keys cascade to profiles and everything
        below it. Uses the service-role client and nothing else does."""
        admin = self._get_admin_client()
        if admin is None:
            return AuthOutcome.failure(NOT_CONFIGURED, "no service key configured")
        try:
            admin.auth.admin.delete_user(user_id)
        except Exception as exc:
            return _classify(exc)
        return AuthOutcome(ok=True, user_id=user_id)


class InMemoryAuthGateway:
    """The same gateway interface on top of the in-memory UserRepository.

    This is the fallback that keeps the app working with no Supabase configured. It
    reads and writes User.password_hash (removed in A8, when this class moves to its
    own {email: hash} dictionary). There are no tokens: sign_in just remembers WHO is
    signed in so update_password knows whose password to change. `user_id` is the
    email here."""

    def __init__(self, users) -> None:
        self._users = users
        self._current_email: str | None = None

    def sign_up(self, name: str, email: str, password: str) -> AuthOutcome:
        email = email.strip().lower()
        if self._users.exists(email):
            return AuthOutcome.failure(ALREADY_REGISTERED, "email already registered")
        self._users.add(User(name=name.strip(), email=email,
                             password_hash=hash_password(password), onboarded=False))
        self._current_email = email
        return AuthOutcome(ok=True, user_id=email, email=email)

    def sign_in(self, email: str, password: str) -> AuthOutcome:
        user = self._users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            return AuthOutcome.failure(INVALID_CREDENTIALS, "wrong email or password")
        self._current_email = user.email
        return AuthOutcome(ok=True, user_id=user.email, email=user.email)

    def sign_out(self) -> AuthOutcome:
        self._current_email = None
        return AuthOutcome(ok=True)

    def update_password(self, new_password: str) -> AuthOutcome:
        user = self._users.get_by_email(self._current_email) if self._current_email else None
        if user is None:
            return AuthOutcome.failure(SESSION_EXPIRED, "nobody is signed in")
        user.password_hash = hash_password(new_password)
        self._users.save(user)
        return AuthOutcome(ok=True, user_id=user.email, email=user.email)

    def restore_session(self, tokens) -> AuthOutcome:
        return AuthOutcome.failure(SESSION_EXPIRED, "in-memory sessions cannot be restored")

    def admin_delete_user(self, user_id: str) -> AuthOutcome:
        if not self._users.delete(user_id):
            return AuthOutcome.failure(UNKNOWN, "account not found")
        if self._current_email == (user_id or "").strip().lower():
            self._current_email = None
        return AuthOutcome(ok=True, user_id=user_id)

    def current_user_id(self) -> str | None:
        return self._current_email
