"""Onboarding page: stepper UI only.
Rules and saving live in OnboardingController; the draft is a Profile model."""
import html

import streamlit as st

from models.profile import Profile
from utils.images import to_data_uri
from views.components.photo_cropper import crop_controls
from views.components.styles import load_css
from views.session import (
    finish_onboarding, get_onboarding_controller, get_profile_controller, refresh_session_user,
)

# NOTE: do NOT call st.set_page_config here. App.py already does it.

STEPS = [
    ("Basic Info", "Personal Info & Major"),
    ("Skills & Portfolio", "Showcase your talents"),
    ("Profile Photo", "Show your face"),
]

# ---------------------------------------------------------------- helpers
def _init_state():
    st.session_state.setdefault("ob_step", 1)
    if not isinstance(st.session_state.get("ob_data"), Profile):
        st.session_state.ob_data = get_onboarding_controller().new_draft()


def _email() -> str:
    return st.session_state.user["email"]


def _go(step: int):
    st.session_state.ob_step = step
    st.rerun()


def _add_item(input_key: str, field_name: str):
    """on_change callback: hand the typed value to the controller, then clear the box."""
    get_onboarding_controller().add_item(
        st.session_state.ob_data, field_name, st.session_state.get(input_key, "")
    )
    st.session_state[input_key] = ""


def _chips(draft: Profile, field_name: str, prefix: str):
    """Pill-shaped buttons; clicking one removes it."""
    items = getattr(draft, field_name)
    if not items:
        return
    with st.container(horizontal=True, key=f"chips_{prefix}"):
        for i, item in enumerate(items):
            if st.button(f"{item}   ✕", key=f"chip_{prefix}_{i}"):
                get_onboarding_controller().remove_item(draft, field_name, i)
                st.rerun()


def _left_panel(step: int):
    steps_html = ""
    for i, (title, sub) in enumerate(STEPS, start=1):
        active = " active" if i == step else ""
        steps_html += (
            f'<div class="ob-step{active}">'
            f'<div class="ob-circle">{i}</div>'
            f'<div><div class="ob-step-title">{title}</div>'
            f'<div class="ob-step-sub">{sub}</div></div></div>'
        )

    with st.container(key="ob_left"):
        st.markdown(
            f"""
            <div class="ob-welcome">Welcome<br>Aboard!</div>
            <div class="ob-welcome-sub">
                Let’s set up your profile so the community can get to know you.
            </div>
            {steps_html}
            """,
            unsafe_allow_html=True,
        )


def _header(title: str, sub: str):
    st.markdown(f'<div class="ob-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="ob-sub">{sub}</div>', unsafe_allow_html=True)


def _nav(step: int):
    """Back / Next row. Returns (back_clicked, next_clicked)."""
    align = "right" if step == 1 else "distribute"
    back = nxt = False
    with st.container(horizontal=True, horizontal_alignment=align, key="nav_row"):
        if step > 1:
            back = st.button("Back", key="nav_back")
        nxt = st.button("Next", key="nav_next")
    return back, nxt


# ---------------------------------------------------------------- steps
def _step_basic(draft: Profile):
    _header("Basic Information", "Tell us more about yourself and what you’re passionate about")
    st.space("small")

    draft.major = st.text_input("Strand / Major / Degree Program", value=draft.major)
    draft.bio = st.text_area(
        "Short Bio", value=draft.bio, height=200, max_chars=Profile.MAX_BIO_LENGTH
    )

    _, nxt = _nav(1)
    if nxt:
        _go(2)


def _step_skills(draft: Profile):
    _header(
        "Skills & Portfolio",
        "Add your skills and links to our work to attract potential clients or collaborators.",
    )

    st.markdown('<div class="ob-h2">Skills</div>', unsafe_allow_html=True)
    with st.container(key="card_skills"):
        st.text_input(
            "Add Skills",
            key="skill_input",
            on_change=_add_item,
            args=("skill_input", "skills"),
            help="Press Enter to add",
        )
        _chips(draft, "skills", "skills")

    st.markdown('<div class="ob-h2">Portfolio & Links</div>', unsafe_allow_html=True)
    with st.container(key="card_portfolio"):
        draft.portfolio = st.text_input("Personal Portfolio", value=draft.portfolio)
        c1, c2 = st.columns(2)
        with c1:
            draft.linkedin = st.text_input("LinkedIn", value=draft.linkedin)
        with c2:
            draft.github = st.text_input("Github", value=draft.github)

    st.markdown('<div class="ob-h2">Professional Socials (at least one)</div>',
                unsafe_allow_html=True)
    with st.container(key="card_socials"):
        st.text_input(
            "Add Social Media Link",
            key="social_input",
            on_change=_add_item,
            args=("social_input", "socials"),
            help="Press Enter to add",
        )
        _chips(draft, "socials", "socials")

    back, nxt = _nav(2)
    if back:
        _go(1)
    if nxt:
        error = get_onboarding_controller().socials_error(draft)
        if error:
            st.error(error)         # stay on this step until one social link is added
        else:
            _go(3)


_PHOTO_KEY = "ob_photo"      # (bytes, mime) of the cropped photo, kept until onboarding ends
_PLACEHOLDER = "👤"


def _remove_photo():
    st.session_state.pop(_PHOTO_KEY, None)


@st.dialog("Upload photo")
def _photo_dialog():
    """Pick a file, crop it with the Profile page's crop box, then use it."""
    ctrl = get_profile_controller()
    file = st.file_uploader("Choose an image", type=["png", "jpg", "jpeg"], key="photo_upload_ob")
    if file is not None:
        error = ctrl.photo_error(file.size)
        if error:
            st.error(error)
            file = None
    chosen = None                                   # (bytes, mime) that will be used
    if file is not None:
        # crop to a square first; if the file can't be cropped, keep the original upload
        chosen = crop_controls(file.getvalue(), key=f"ob_{file.file_id}")
        if chosen is None:
            chosen = (file.getvalue(), file.type)
            st.image(file, width=160)
    with st.container(horizontal=True, horizontal_alignment="distribute"):
        if st.button("Cancel", key="ob_photo_cancel"):
            st.rerun()
        if st.button("Use photo", key="ob_photo_use", disabled=chosen is None):
            st.session_state[_PHOTO_KEY] = chosen
            st.rerun()


def _avatar_circle():
    """The round preview: the chosen photo, or a placeholder until there is one."""
    photo = st.session_state.get(_PHOTO_KEY)
    if photo:
        style = f"background-image:url({html.escape(to_data_uri(*photo), quote=True)})"
        inner = ""
    else:
        style, inner = "", _PLACEHOLDER
    st.markdown(f'<div class="ob-avatar" style="{style}">{inner}</div>', unsafe_allow_html=True)


def _step_photo(draft: Profile):
    _header(
        "Profile Photo",
        "Add a photo so other students recognise you. You can skip this and add one later "
        "from your Profile page.",
    )

    has_photo = _PHOTO_KEY in st.session_state
    with st.container(key="ob_avatar_box"):
        _avatar_circle()
        if st.button("Change photo" if has_photo else "Upload photo", key="ob_photo_open",
                     icon=":material/photo_camera:"):
            _photo_dialog()
        if has_photo:
            st.button("Remove photo", key="ob_photo_remove", type="tertiary",
                      on_click=_remove_photo)

    ctrl = get_profile_controller()
    back, nxt = _nav(3)
    if back:
        _go(2)
    if nxt:
        email = _email()
        if get_onboarding_controller().socials_error(draft):
            _go(2)                  # safety net: the social link is required
        if get_onboarding_controller().complete(email, draft):
            photo = st.session_state.get(_PHOTO_KEY)
            # after complete(): saving the draft would otherwise overwrite the photo
            error = ctrl.update_photo(email, *photo) if photo else None
            if error:
                # the profile is saved; stay here so they can retry or press Remove photo
                st.error(f"Your photo couldn't be saved: {error}")
                return
            _remove_photo()
            user = ctrl.get_user(email)
            if user:
                refresh_session_user(user)       # so the dashboard shows the photo right away
        finish_onboarding()
        st.rerun()


# ---------------------------------------------------------------- entry
def render_onboarding():
    _init_state()
    step = st.session_state.ob_step
    draft = st.session_state.ob_data

    load_css("onboarding")
    _left_panel(step)

    with st.container(key="ob_right"):
        if step == 1:
            _step_basic(draft)
        elif step == 2:
            _step_skills(draft)
        else:
            _step_photo(draft)


# Only run onboarding while the user hasn't finished it.
if not st.session_state.get("onboarding_complete", False):
    render_onboarding()
