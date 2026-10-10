"""Create a Listing: 4-step wizard shown inside the Marketplace page.

Flow:  1. Type (Gig / Rental)  ->  1b. Deliverable type (Gigs only)
       2. Details  ->  3. Upload Images  ->  4. Review and Post

Layout only. Step order, validation and posting live in ListingWizardController;
the draft lives in session_state (see views/session.py). Styles:
views/styles/listing_wizard.css (uses --orange from marketplace.css).
"""
from html import escape

import streamlit as st

from models.listing import (
    MAX_IMAGES, PROJECT_DELIVERABLE, RATE_TYPES, RENTAL, GIG, SERVICE_DELIVERABLE,
)
from models.listing_draft import PROGRESS_LABELS, DraftImage, ListingDraft, WizardStep
from repositories.errors import RepositoryError
from views.components.repo_errors import show_error
from views.components.styles import load_css
from views.session import (
    close_listing_wizard, get_listing_draft, get_listing_wizard_controller,
)


# ==========================================
# CALLBACKS
# ==========================================

def _pick_category(value: str) -> None:
    get_listing_wizard_controller().choose_category(get_listing_draft(), value)


def _pick_deliverable(value: str) -> None:
    get_listing_wizard_controller().choose_deliverable(get_listing_draft(), value)


# ==========================================
# SMALL BUILDING BLOCKS
# ==========================================

def _progress_html(active: int) -> str:
    steps = "".join(
        f"<div class='sh-wiz-step{' active' if i == active else ''}'>"
        f"<span class='num'>{i}</span><span class='lbl'>{label}</span></div>"
        for i, label in enumerate(PROGRESS_LABELS, start=1)
    )
    return f"<div class='sh-wiz-progress'><div class='sh-wiz-ptitle'>PROGRESS</div>{steps}</div>"


def _heading(title: str, caption: str = "") -> None:
    cap = f"<div class='sh-wiz-cap'>{escape(caption)}</div>" if caption else ""
    st.markdown(f"<div class='sh-wiz-h'>{escape(title)}</div>{cap}", unsafe_allow_html=True)


def _choice(key: str, icon: str, title: str, sub: str, selected: bool, on_click, value: str) -> None:
    """A big clickable card (HTML look + invisible button on top)."""
    with st.container(key=f"choice_{key}"):
        st.markdown(
            f"<div class='sh-choice{' selected' if selected else ''}'>"
            f"<div class='ico'>{icon}</div>"
            f"<div class='ttl'>{escape(title)}</div>"
            f"<div class='sub'>{escape(sub)}</div></div>",
            unsafe_allow_html=True,
        )
        st.button(f"Select {title}", key=f"pick_{key}", on_click=on_click, args=(value,))


def _nav(next_label: str = "Next Step", next_key: str = "wiz_next", show_back: bool = True):
    """Go Back (left, optional) and Next Step / Post (right). Returns (back, next) clicks."""
    with st.container(key="wiz_nav"):
        left, right = st.columns(2)
        with left:
            back = st.button("Go Back", key="wiz_back") if show_back else False
        with right:
            nxt = st.button(next_label, key=next_key)
    return back, nxt


def _go_back(wizard, draft: ListingDraft) -> None:
    wizard.back(draft)
    st.rerun()


def _go_next(wizard, draft: ListingDraft) -> None:
    """Validate the step; show the error, or move on."""
    error = wizard.next(draft)
    if error:
        st.error(error)
    else:
        st.rerun()


# ==========================================
# SCREENS
# ==========================================

def _screen_type(wizard, draft: ListingDraft) -> None:
    _heading("What are you listing?", "Choose what type of service are you offering.")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        _choice("gig", "\U0001F91D", "Offer a Gig", "Tutoring, design, etc.",
                draft.category == GIG, _pick_category, GIG)
    with c2:
        _choice("rental", "\U0001F4C5", "Offer a Rental", "Camera, Books, etc.",
                draft.category == RENTAL, _pick_category, RENTAL)

    _, nxt = _nav(show_back=False)   # first step: no Go Back
    if nxt:
        _go_next(wizard, draft)


def _screen_deliverable(wizard, draft: ListingDraft) -> None:
    _heading("What are you listing?", "Choose what type of service are you offering.")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        _choice("service", "\U0001F6CE️", "Service Deliverables", "Tutoring etc.",
                draft.deliverable == SERVICE_DELIVERABLE, _pick_deliverable, SERVICE_DELIVERABLE)
    with c2:
        _choice("project", "\U0001F4CB", "Project Deliverables", "Logo Making etc.",
                draft.deliverable == PROJECT_DELIVERABLE, _pick_deliverable, PROJECT_DELIVERABLE)

    back, nxt = _nav()
    if back:
        _go_back(wizard, draft)
    if nxt:
        _go_next(wizard, draft)


def _screen_details(wizard, draft: ListingDraft) -> None:
    _heading("Details")

    title = st.text_input("Title", value=draft.title, key="wiz_title")
    rate_type = st.selectbox("Rate Type", RATE_TYPES,
                             index=RATE_TYPES.index(draft.rate_type), key="wiz_rate_type")
    rate = st.number_input("Rate (₱)", min_value=0.0, step=50.0,
                           value=float(draft.rate), key="wiz_rate")
    description = st.text_area(f"Add a description of your {draft.noun}",
                               value=draft.description, height=110, key="wiz_desc")

    back, nxt = _nav()
    if back or nxt:
        wizard.save_details(draft, title, rate_type, rate, description)
    if back:
        _go_back(wizard, draft)
    if nxt:
        _go_next(wizard, draft)


def _screen_media(wizard, draft: ListingDraft) -> None:
    _heading("Upload Images", f"Upload up to {MAX_IMAGES} images of your {draft.noun}")

    files = st.file_uploader("Upload images", type=["png", "jpg", "jpeg", "webp"],
                             accept_multiple_files=True, key="wiz_files",
                             label_visibility="collapsed")
    uploaded, truncated = wizard.limit_images(
        [DraftImage(f.getvalue(), f.name, f.type or "image/png") for f in files]
    )
    if truncated:
        st.warning(f"You can add up to {MAX_IMAGES} images, so only the first "
                   f"{MAX_IMAGES} will be used.")

    # New uploads replace the saved images; otherwise keep what was saved.
    shown = uploaded or draft.images
    if shown:
        st.image([img.data for img in shown], width=110)
        if not uploaded:
            st.caption("Current images (upload new ones to replace them)")
            if st.button("Remove images", key="wiz_clear"):
                wizard.clear_images(draft)
                st.rerun()

    back, nxt = _nav()
    if back or nxt:
        wizard.set_images(draft, shown)
    if back:
        _go_back(wizard, draft)
    if nxt:
        _go_next(wizard, draft)


def _screen_review(wizard, draft: ListingDraft) -> None:
    _heading("Review")

    chip = f"<span class='sh-wiz-chip'>{escape(draft.deliverable)}</span>" if draft.deliverable else ""
    pill_cls = "" if draft.is_gig else " rental"
    rows = [
        ("Title", draft.title, False),
        ("Rate Type", draft.rate_type, False),
        ("Rate", f"₱{draft.rate:.0f}", False),
        ("Description", draft.description or "—", True),
        ("Images", ", ".join(i.name for i in draft.images) or "No images uploaded", True),
    ]
    fields = "".join(
        f"<div class='sh-wiz-label'>{label}</div>"
        f"<div class='sh-wiz-value{' multi' if multi else ''}'>{escape(value)}</div>"
        for label, value, multi in rows
    )
    st.markdown(
        f"<div class='sh-wiz-typerow'>Type of Listing: "
        f"<span class='sh-wiz-pill{pill_cls}'>{'Gigs' if draft.is_gig else 'Rentals'}</span>{chip}</div>"
        f"{fields}",
        unsafe_allow_html=True,
    )

    back, post = _nav(next_label="Post", next_key="wiz_post")
    if back:
        _go_back(wizard, draft)
    if post:
        user = st.session_state.get("user") or {}
        try:
            with st.spinner("Posting your listing..."):
                result = wizard.post(draft, user.get("email", ""))
        except RepositoryError as exc:       # the draft is untouched: they can press Post again
            show_error(exc, "Couldn't post your listing.")
            return
        if not result.ok:
            st.error(result.error)
        else:
            close_listing_wizard()
            st.session_state.selected_listing_id = result.listing.id   # open the new listing
            st.toast("Your listing has been posted!")
            st.rerun()


SCREENS = {
    WizardStep.TYPE: _screen_type,
    WizardStep.DELIVERABLE: _screen_deliverable,
    WizardStep.DETAILS: _screen_details,
    WizardStep.MEDIA: _screen_media,
    WizardStep.REVIEW: _screen_review,
}

# ==========================================
# PAGE
# ==========================================

def render_create_listing() -> None:
    """Draw the whole 'Create a Listing' page (the draft must already exist)."""
    draft = get_listing_draft()
    if draft is None:
        return
    wizard = get_listing_wizard_controller()

    load_css("listing_wizard")

    # Return to the Marketplace from any step (key "back_btn" reuses the pill
    # style of the Back button on the listing detail page)
    st.button("Back to Marketplace", key="back_btn", on_click=close_listing_wizard)

    st.markdown(
        "<div class='sh-wiz-title'>Create a Listing</div>"
        "<div class='sh-wiz-sub'>Share your skills or items with the community!</div>",
        unsafe_allow_html=True,
    )

    left, right = st.columns([1, 2.3], gap="large")
    with left:
        st.markdown(_progress_html(draft.progress_number), unsafe_allow_html=True)
    with right:
        with st.container(key="wiz_card"):
            SCREENS[draft.step](wizard, draft)
