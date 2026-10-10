"""User domain model. Pure data + behaviour, no Streamlit, no storage."""
from dataclasses import dataclass, field

from models.profile import Profile


@dataclass
class User:
    name: str
    email: str            # always stored lower-cased
    onboarded: bool = False
    profile: Profile = field(default_factory=Profile)

    def to_session_dict(self) -> dict:
        """Shape the rest of the app currently expects in session_state.user."""
        return {"name": self.name, "email": self.email}
