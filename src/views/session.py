"""Glue between controllers and Streamlit's session_state.
Only the view layer talks to session_state; controllers never do."""
import streamlit as st

from controllers.auth_controller import AuthController
from controllers.onboarding_controller import OnboardingController
from models.user import User
from repositories.user_repository import UserRepository


def get_user_repository() -> UserRepository:
    """One repository per browser session, shared by every controller."""
    if "user_repository" not in st.session_state:
        st.session_state.user_repository = UserRepository.seeded()
    return st.session_state.user_repository


def get_auth_controller() -> AuthController:
    return AuthController(get_user_repository())


def get_onboarding_controller() -> OnboardingController:
    return OnboardingController(get_user_repository())


def start_session(user: User, reset_onboarding: bool = False) -> None:
    st.session_state.logged_in = True
    st.session_state.user = user.to_session_dict()
    st.session_state.onboarding_complete = user.onboarded
    if reset_onboarding:
        st.session_state.pop("ob_step", None)
        st.session_state.pop("ob_data", None)


def finish_onboarding() -> None:
    st.session_state.onboarding_complete = True
