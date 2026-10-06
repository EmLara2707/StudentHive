"""Onboarding page: stepper UI only.
Rules and saving live in OnboardingController; the draft is a Profile model."""
import streamlit as st

from models.profile import Profile
from views.components.styles import load_css
from views.session import finish_onboarding, get_onboarding_controller

# NOTE: do NOT call st.set_page_config here. App.py already does it.

STEPS = [
    ("Basic Info", "Personal Info & Major"),
    ("Skills & Portfolio", "Showcase your talents"),
    ("ID Verification", "Student ID Upload"),
]

CLOUD_ICON = (
    '<svg width="120" height="120" viewBox="0 0 24 24" fill="none" stroke="#7d7d7d" '
    'stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M4 14.9A7 7 0 1 1 15.7 8h1.8a4.5 4.5 0 0 1 2.5 8.2"/>'
    '<path d="M12 12v9"/><path d="m16 16-4-4-4 4"/></svg>'
)


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

        # TEMP (testing only): delete this block + the .st-key-skip_ob CSS in
        # onboarding.css + OnboardingController.skip() before launch
        if st.button("Skip onboarding (testing)", key="skip_ob"):
            get_onboarding_controller().skip(_email())
            finish_onboarding()
            st.rerun()


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

    st.markdown('<div class="ob-h2">Professional Socials</div>', unsafe_allow_html=True)
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
        _go(3)


def _step_id(draft: Profile):
    _header(
        "ID Verification",
        "Upload your ID to verify that you are part of the institution. "
        "Please ensure the information is clear and visible",
    )

    with st.container(key="upload_box"):
        st.markdown(
            f'<div style="text-align:center">{CLOUD_ICON}'
            '<div class="ob-upload-text">Drag and drop your image here<br>or</div></div>',
            unsafe_allow_html=True,
        )
        uploaded = st.file_uploader(
            "Student ID",
            type=["png", "jpg", "jpeg"],
            label_visibility="collapsed",
            key="id_upload",
        )
    st.markdown('<div class="ob-upload-hint">PNG or JPG</div>', unsafe_allow_html=True)

    back, nxt = _nav(3)
    if back:
        _go(2)
    if nxt:
        # The image itself is not stored; verification is delegated to a
        # third-party service (see the TODO in OnboardingController.complete).
        get_onboarding_controller().complete(
            _email(), draft, id_submitted=uploaded is not None
        )
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
            _step_id(draft)


# Only run onboarding while the user hasn't finished it.
if not st.session_state.get("onboarding_complete", False):
    render_onboarding()
