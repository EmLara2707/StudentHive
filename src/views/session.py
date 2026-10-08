"""Glue between controllers and Streamlit's session_state.
Only the view layer talks to session_state; controllers never do."""
import streamlit as st

from controllers.auth_controller import AuthController
from controllers.booking_controller import BookingController
from controllers.dashboard_controller import DashboardController
from controllers.listing_controller import ListingController
from controllers.listing_wizard_controller import ListingWizardController
from controllers.marketplace_controller import MarketplaceController
from controllers.onboarding_controller import OnboardingController
from controllers.profile_controller import ProfileController
from controllers.public_profile_controller import PublicProfileController
from controllers.transaction_controller import TransactionController
from models.listing_draft import ListingDraft
from models.user import User
from repositories import factory
from repositories.listing_repository import ListingRepository
from repositories.review_repository import ReviewRepository
from repositories.transaction_repository import TransactionRepository
from repositories.user_repository import UserRepository

# ---- Supabase: one client PER BROWSER SESSION, kept in session_state ----
# Never cache a user's client with st.cache_resource: it carries that user's token.
_CLIENT_KEY = "supabase_client"
_ADMIN_KEY = "supabase_admin_client"
_TOKENS_KEY = "auth_tokens"          # (access_token, refresh_token) of the signed-in user


def _supabase_secrets() -> dict | None:
    """The [supabase] section of .streamlit/secrets.toml, or None when this machine
    has no Supabase configured (the app then runs on the in-memory repositories)."""
    try:
        section = st.secrets["supabase"]
        return {
            "url": section["url"],
            "anon_key": section["anon_key"],
            "service_key": section.get("service_key"),
        }
    except (FileNotFoundError, KeyError):
        return None


def get_supabase_client():
    """This browser session's Supabase client (carrying the stored token, if any),
    or None when Supabase isn't configured."""
    client = st.session_state.get(_CLIENT_KEY)
    if client is not None:
        return client
    config = _supabase_secrets()
    if config is None:
        return None
    from repositories.supabase_client import create_client, with_token
    client = create_client(config["url"], config["anon_key"])
    tokens = st.session_state.get(_TOKENS_KEY)
    if tokens:
        try:
            with_token(client, *tokens)
        except Exception:                      # expired beyond refresh: sign in again
            st.session_state.pop(_TOKENS_KEY, None)
    st.session_state[_CLIENT_KEY] = client
    return client


def get_admin_client():
    """Service-role client, or None if no service key is configured. Only for deleting
    accounts and seed scripts; never pass it to a view."""
    client = st.session_state.get(_ADMIN_KEY)
    if client is not None:
        return client
    config = _supabase_secrets()
    if config is None or not config["service_key"]:
        return None
    from repositories.supabase_client import create_admin_client
    client = create_admin_client(config["url"], config["service_key"])
    st.session_state[_ADMIN_KEY] = client
    return client


def store_auth_tokens(access_token: str, refresh_token: str) -> None:
    """Remember the signed-in user's tokens for this browser session."""
    st.session_state[_TOKENS_KEY] = (access_token, refresh_token)


def get_auth_tokens() -> tuple[str, str] | None:
    return st.session_state.get(_TOKENS_KEY)


# ---- repositories: one of each per browser session ----
# What gets built (in-memory or Supabase) is decided in repositories/factory_a.py
# and factory_b.py: one flag per repository, each owned by one person.
def get_user_repository() -> UserRepository:
    if "user_repository" not in st.session_state:
        st.session_state.user_repository = factory.build_user_repository(get_supabase_client())
    return st.session_state.user_repository


def get_listing_repository() -> ListingRepository:
    if "listing_repository" not in st.session_state:
        st.session_state.listing_repository = factory.build_listing_repository(
            get_supabase_client())
    return st.session_state.listing_repository


def get_review_repository() -> ReviewRepository:
    if "review_repository" not in st.session_state:
        st.session_state.review_repository = factory.build_review_repository(
            get_supabase_client())
    return st.session_state.review_repository


def get_transaction_repository() -> TransactionRepository:
    if "transaction_repository" not in st.session_state:
        st.session_state.transaction_repository = factory.build_transaction_repository(
            get_supabase_client())
    return st.session_state.transaction_repository


def get_auth_gateway():
    """What AuthController signs people in with (None until Person A's A2 lands)."""
    if "auth_gateway" not in st.session_state:
        st.session_state.auth_gateway = factory.build_auth_gateway(
            get_supabase_client(), get_admin_client)
    return st.session_state.auth_gateway


# ---- controllers (stateless, cheap to build) ----
def get_auth_controller() -> AuthController:
    return AuthController(
        get_user_repository(), get_listing_repository(), get_review_repository(),
        get_transaction_repository(),
    )


def get_onboarding_controller() -> OnboardingController:
    return OnboardingController(get_user_repository())


def get_profile_controller() -> ProfileController:
    return ProfileController(get_user_repository(), get_review_repository())


def get_public_profile_controller() -> PublicProfileController:
    return PublicProfileController(
        get_user_repository(), get_review_repository(), get_listing_repository()
    )


def get_listing_controller() -> ListingController:
    return ListingController(get_listing_repository())


def get_listing_wizard_controller() -> ListingWizardController:
    return ListingWizardController(get_listing_controller())


def get_marketplace_controller() -> MarketplaceController:
    return MarketplaceController(get_listing_repository(), get_user_repository())


def get_booking_controller() -> BookingController:
    return BookingController(
        get_marketplace_controller(), get_review_repository(), get_transaction_repository(),
        get_user_repository(),
    )


def get_dashboard_controller() -> DashboardController:
    return DashboardController(get_listing_repository(), get_transaction_repository())


def get_transaction_controller() -> TransactionController:
    return TransactionController(
        get_transaction_repository(), get_user_repository(), get_review_repository()
    )


def get_current_email() -> str:
    """Email of the logged-in user ('' when nobody is logged in)."""
    return (st.session_state.get("user") or {}).get("email", "")


# ---- session lifecycle ----
def start_session(user: User, reset_onboarding: bool = False) -> None:
    st.session_state.logged_in = True
    st.session_state.user = user.to_session_dict()
    st.session_state.onboarding_complete = user.onboarded
    if reset_onboarding:
        st.session_state.pop("ob_step", None)
        st.session_state.pop("ob_data", None)


# The in-memory repositories ARE the "database" for now, so a logout must not wipe them
# (registered accounts would disappear). A Supabase-backed one (in_memory = False) is
# tied to one person's client, so it IS dropped. Everything else belongs to the person
# who just left: wizard draft, open booking page, typed text, open profile, selections...
_REPOSITORY_KEYS = (
    "user_repository", "listing_repository", "review_repository", "transaction_repository",
    "auth_gateway",
)


def _sign_out_of_supabase() -> None:
    client = st.session_state.get(_CLIENT_KEY)
    if client is None:
        return
    try:
        client.auth.sign_out({"scope": "local"})   # this session only, not their other devices
    except Exception:
        pass            # token already expired or no network: the client is dropped anyway


def end_session() -> None:
    """Log out and forget everything the previous person was doing."""
    _sign_out_of_supabase()
    keep = {key for key in _REPOSITORY_KEYS
            if getattr(st.session_state.get(key), "in_memory", True)}
    # everything else goes, including the Supabase client(s) and the stored tokens
    for key in list(st.session_state.keys()):
        if key not in keep:
            del st.session_state[key]
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.onboarding_complete = False


def refresh_session_user(user: User) -> None:
    """Keep session_state.user (read by other pages) in sync after a profile edit."""
    st.session_state.user = user.to_session_dict()


def finish_onboarding() -> None:
    st.session_state.onboarding_complete = True


# ---- create-a-listing wizard: one draft while the wizard is open, else None ----
_DRAFT_KEY = "listing_draft"


def start_listing_wizard() -> None:
    """'Add a Listing' clicked: open the wizard with a fresh draft."""
    st.session_state[_DRAFT_KEY] = get_listing_wizard_controller().new_draft()


def close_listing_wizard() -> None:
    st.session_state[_DRAFT_KEY] = None


def is_creating_listing() -> bool:
    return st.session_state.get(_DRAFT_KEY) is not None


def get_listing_draft() -> ListingDraft | None:
    return st.session_state.get(_DRAFT_KEY)
