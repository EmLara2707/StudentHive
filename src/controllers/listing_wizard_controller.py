"""Rules of the Create-a-Listing wizard: step order, per-step validation,
and posting the finished draft. Never imports streamlit."""
from controllers.listing_controller import ListingController, ListingResult
from models.listing import (
    CATEGORIES, DELIVERABLES, GIG, MAX_IMAGES, default_rate_type,
)
from models.listing_draft import DraftImage, ListingDraft, WizardStep


class ListingWizardController:
    def __init__(self, listings: ListingController) -> None:
        self._listings = listings

    # ---- draft lifecycle ----
    def new_draft(self) -> ListingDraft:
        return ListingDraft()

    # ---- choices ----
    def choose_category(self, draft: ListingDraft, category: str) -> None:
        """Pick Gig or Rental. Changing the choice resets the deliverable and
        the default rate type (Gigs hourly, Rentals daily)."""
        if category not in CATEGORIES or draft.category == category:
            return
        draft.category = category
        draft.deliverable = None
        draft.rate_type = default_rate_type(category)

    def choose_deliverable(self, draft: ListingDraft, deliverable: str) -> None:
        if deliverable in DELIVERABLES:
            draft.deliverable = deliverable

    def save_details(self, draft: ListingDraft, title: str, rate_type: str,
                     rate: float, description: str) -> None:
        """Remember the form values (also when validation then fails)."""
        draft.title = title
        draft.rate_type = rate_type
        draft.rate = rate
        draft.description = description

    # ---- images ----
    def limit_images(self, images: list[DraftImage]) -> tuple[list[DraftImage], bool]:
        """Keep at most MAX_IMAGES. Returns (kept, was_truncated)."""
        return images[:MAX_IMAGES], len(images) > MAX_IMAGES

    def set_images(self, draft: ListingDraft, images: list[DraftImage]) -> None:
        draft.images = list(images)

    def clear_images(self, draft: ListingDraft) -> None:
        draft.images = []

    # ---- navigation ----
    def next(self, draft: ListingDraft) -> str | None:
        """Validate the current step and move on. Returns an error message
        (and stays on the step) or None after advancing."""
        step = draft.step
        if step is WizardStep.TYPE:
            if not draft.category:
                return "Please choose Gig or Rental to continue."
            # the deliverable question only applies to Gigs
            draft.step = WizardStep.DELIVERABLE if draft.is_gig else WizardStep.DETAILS
        elif step is WizardStep.DELIVERABLE:
            if not draft.deliverable:
                return "Please choose a deliverable type to continue."
            draft.step = WizardStep.DETAILS
        elif step is WizardStep.DETAILS:
            if not draft.title.strip():
                return "Please add a title."
            if draft.rate <= 0:
                return "Please enter a rate greater than 0."
            draft.step = WizardStep.MEDIA
        elif step is WizardStep.MEDIA:
            draft.step = WizardStep.REVIEW
        return None

    def back(self, draft: ListingDraft) -> None:
        step = draft.step
        if step is WizardStep.DELIVERABLE:
            draft.step = WizardStep.TYPE
        elif step is WizardStep.DETAILS:
            draft.step = WizardStep.DELIVERABLE if draft.is_gig else WizardStep.TYPE
        elif step is WizardStep.MEDIA:
            draft.step = WizardStep.DETAILS
        elif step is WizardStep.REVIEW:
            draft.step = WizardStep.MEDIA

    # ---- posting ----
    def post(self, draft: ListingDraft, owner_email: str) -> ListingResult:
        """Create the listing from the draft (ListingController validates again)."""
        return self._listings.create(
            owner_email=owner_email,
            title=draft.title,
            category=draft.category or "",
            rate_type=draft.rate_type,
            rate=draft.rate,
            description=draft.description,
            deliverable=(draft.deliverable or "") if draft.category == GIG else "",
            images=[(img.data, img.mime) for img in draft.images],
        )
