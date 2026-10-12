"""Onboarding use-cases. No Streamlit, no session_state."""
import copy

from models.profile import Profile
from repositories.user_repository import UserRepository

_LIST_FIELDS = {"skills", "socials"}


class OnboardingController:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def new_draft(self) -> Profile:
        return Profile()

    # ---- list editing (skills / socials) ----
    def add_item(self, draft: Profile, field_name: str, value: str) -> bool:
        """Add a de-duplicated, trimmed entry. Returns True if it was added."""
        if field_name not in _LIST_FIELDS:
            raise ValueError(f"Unknown list field: {field_name}")
        value = (value or "").strip()
        items: list[str] = getattr(draft, field_name)
        if not value or value in items:
            return False
        items.append(value)
        return True

    def remove_item(self, draft: Profile, field_name: str, index: int) -> None:
        if field_name not in _LIST_FIELDS:
            raise ValueError(f"Unknown list field: {field_name}")
        items: list[str] = getattr(draft, field_name)
        if 0 <= index < len(items):
            items.pop(index)

    # ---- rules ----
    SOCIALS_REQUIRED_ERROR = "Add at least one social media link so other students can reach you."

    def socials_error(self, draft: Profile) -> str | None:
        """Step 2 needs at least one social media contact. Returns the message, or None if fine."""
        return None if any(s.strip() for s in draft.socials) else self.SOCIALS_REQUIRED_ERROR

    # ---- finishing ----
    def complete(self, email: str, draft: Profile) -> bool:
        """Save the draft onto the user and mark them onboarded."""
        user = self._users.get_by_email(email)
        if user is None or self.socials_error(draft):
            return False

        profile = copy.deepcopy(draft)
        profile.major = profile.major.strip()
        profile.bio = profile.bio.strip()[: Profile.MAX_BIO_LENGTH]

        user.profile = profile
        user.onboarded = True
        self._users.save(user)
        return True
