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
from models.listing_draft import ListingDraft
from models.user import User
from repositories.booking_repository import BookingRepository
from repositories.event_repository import EventRepository
from repositories.listing_repository import ListingRepository
from repositories.review_repository import ReviewRepository
from repositories.user_repository import UserRepository


# ---- repositories: one of each per browser session ----
def get_user_repository() -> UserRepository:
    if "user_repository" not in st.session_state:
        st.session_state.user_repository = UserRepository.seeded()
    return st.session_state.user_repository


def get_listing_repository() -> ListingRepository:
    if "listing_repository" not in st.session_state:
        st.session_state.listing_repository = ListingRepository.seeded()
    return st.session_state.listing_repository


def get_review_repository() -> ReviewRepository:
    if "review_repository" not in st.session_state:
        st.session_state.review_repository = ReviewRepository.seeded()
    return st.session_state.review_repository


def get_booking_repository() -> BookingRepository:
    if "booking_repository" not in st.session_state:
        st.session_state.booking_repository = BookingRepository()
    return st.session_state.booking_repository


def get_event_repository() -> EventRepository:
    if "event_repository" not in st.session_state:
        st.session_state.event_repository = EventRepository.seeded()
    return st.session_state.event_repository


# ---- controllers (stateless, cheap to build) ----
def get_auth_controller() -> AuthController:
    return AuthController(get_user_repository())


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
        get_marketplace_controller(), get_review_repository(), get_booking_repository()
    )


def get_dashboard_controller() -> DashboardController:
    return DashboardController(get_listing_repository(), get_event_repository())


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


def end_session() -> None:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.onboarding_complete = False
    st.session_state.pop("ob_step", None)
    st.session_state.pop("ob_data", None)


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
