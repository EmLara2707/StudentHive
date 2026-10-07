"""A listing that is still being created in the wizard.
Pure data + behaviour: no Streamlit, no storage."""
from dataclasses import dataclass, field
from enum import Enum

from models.listing import DEFAULT_GIG_RATE_TYPE, GIG


class WizardStep(str, Enum):
    TYPE = "type"
    DELIVERABLE = "deliverable"      # Gigs only
    DETAILS = "details"
    MEDIA = "media"
    REVIEW = "review"


# The four numbered circles in the progress card; the Gig-only deliverable
# question counts as part of step 1.
PROGRESS_LABELS = ("Type of Listing", "Details", "Upload Images", "Review and Post")
_PROGRESS_NUMBER = {
    WizardStep.TYPE: 1,
    WizardStep.DELIVERABLE: 1,
    WizardStep.DETAILS: 2,
    WizardStep.MEDIA: 3,
    WizardStep.REVIEW: 4,
}


@dataclass(frozen=True)
class DraftImage:
    """One uploaded picture, kept as raw bytes until the listing is posted."""
    data: bytes
    name: str
    mime: str = "image/png"


@dataclass
class ListingDraft:
    step: WizardStep = WizardStep.TYPE
    category: str | None = None          # "Gig" or "Rental"
    deliverable: str | None = None       # Gigs only
    title: str = ""
    rate_type: str = DEFAULT_GIG_RATE_TYPE
    rate: float = 100.0
    description: str = ""
    images: list[DraftImage] = field(default_factory=list)

    @property
    def is_gig(self) -> bool:
        return self.category == GIG

    @property
    def progress_number(self) -> int:
        return _PROGRESS_NUMBER[self.step]

    @property
    def noun(self) -> str:
        """Word used in captions: 'services' for Gigs, 'item' for Rentals."""
        return "services" if self.is_gig else "item"
