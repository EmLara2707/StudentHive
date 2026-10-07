"""Profile domain model: what a user fills in during onboarding / on the Profile page."""
from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar


class IdVerificationStatus(str, Enum):
    NOT_SUBMITTED = "not_submitted"
    PENDING = "pending"      # submitted, waiting on the third-party verifier
    VERIFIED = "verified"
    REJECTED = "rejected"


@dataclass
class Profile:
    MAX_BIO_LENGTH: ClassVar[int] = 500        # onboarding form cap
    MAX_BIO_EDIT_LENGTH: ClassVar[int] = 500   # Profile page editor cap

    major: str = ""
    bio: str = ""
    skills: list[str] = field(default_factory=list)
    portfolio: str = ""
    linkedin: str = ""
    github: str = ""
    socials: list[str] = field(default_factory=list)
    id_status: IdVerificationStatus = IdVerificationStatus.NOT_SUBMITTED
    photo: bytes | None = None
    photo_mime: str | None = None
