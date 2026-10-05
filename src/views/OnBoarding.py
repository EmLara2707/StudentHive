import streamlit as st

# NOTE: do NOT call st.set_page_config here. app.py already does it.

STEPS = [
    ("Basic Info", "Personal Info & Major"),
    ("Skills & Portfolio", "Showcase your talents"),
    ("ID Verification", "Student ID Upload"),
]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Montserrat:wght@700&display=swap');

:root {
    --teal-bg: #0e9486;
    --teal: #0f6b62;
    --teal-hover: #0b5750;
    --teal-line: #0b6b62;
    --teal-ring: #1bbfae;
    --ink: #3a3d3f;
    --muted: #5b6770;
    --line: #dcdfe2;
    --chip: #9fd9f5;
}

html, body, .stApp, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background: #ffffff;
}

/* ---------- page frame ---------- */
/* the page itself scrolls (right side); the left panel is position: fixed */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    overflow: auto !important;
}

[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}

[data-testid="stMainBlockContainer"],
.block-container {
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100% !important;
}

/* ---------- left panel (static) ---------- */
.st-key-ob_left {
    position: fixed;
    top: 0;
    left: 0;
    width: 37%;
    height: 100vh;
    background: var(--teal-bg);
    padding: 0 3rem 0 5.6vw;
    display: flex;
    flex-direction: column;
    justify-content: center;
    z-index: 100;
    overflow: hidden;
}
.ob-welcome {
    font-family: 'Montserrat', sans-serif;
    font-weight: 700;
    font-size: clamp(2.4rem, 3.4vw, 3.6rem);
    line-height: 1.3;
    color: #ffffff;
    margin: 0 0 1.2rem 0;
}
.ob-welcome-sub {
    font-size: clamp(1.1rem, 1.5vw, 1.6rem);
    line-height: 1.6;
    color: rgba(255, 255, 255, 0.75);
    max-width: 30rem;
    margin-bottom: 4rem;
}

/* stepper */
.ob-step {
    position: relative;
    display: flex;
    align-items: center;
    gap: 1.1rem;
    padding-bottom: 1.6rem;
}
.ob-step:last-child { padding-bottom: 0; }
.ob-step:not(:last-child)::after {
    content: "";
    position: absolute;
    left: 25px;
    top: 52px;
    width: 3px;
    height: calc(100% - 52px);
    background: var(--teal-line);
}
.ob-circle {
    flex: 0 0 52px;
    width: 52px;
    height: 52px;
    border-radius: 50%;
    border: 3px solid var(--teal-ring);
    color: var(--teal-ring);
    font-family: 'Montserrat', sans-serif;
    font-weight: 700;
    font-size: 1.35rem;
    display: flex;
    align-items: center;
    justify-content: center;
    box-sizing: border-box;
}
.ob-step.active .ob-circle {
    background: #ffffff;
    color: var(--teal-bg);
    box-shadow: 0 0 0 3px var(--teal-ring);
}
.ob-step-title {
    font-family: 'Montserrat', sans-serif;
    font-weight: 700;
    font-size: clamp(1.1rem, 1.6vw, 1.7rem);
    color: #ffffff;
    line-height: 1.2;
}
.ob-step-sub {
    font-size: clamp(0.85rem, 1vw, 1rem);
    color: rgba(255, 255, 255, 0.85);
    margin-top: 0.25rem;
}

/* ---------- right panel (scrolls) ---------- */
.st-key-ob_right {
    margin-left: 37%;
    width: 63% !important;        /* 100% - the 37% left panel, so it never overflows */
    max-width: 63% !important;
    box-sizing: border-box;
    padding: 7vh 4rem 8vh 3.5rem;
    overflow-x: hidden;
}
/* never allow a sideways scrollbar */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    overflow-x: hidden !important;
}

/* TEMP: skip-onboarding button (testing only) */
.st-key-skip_ob { margin-top: 2.5rem; }
.st-key-skip_ob button {
    background: transparent !important;
    border: 2px dashed rgba(255, 255, 255, 0.6) !important;
    border-radius: 14px !important;
    min-height: 44px;
    padding: 0.3rem 1.2rem !important;
}
.st-key-skip_ob button p {
    color: #ffffff !important;
    font-size: 0.95rem;
    font-weight: 500;
}
.st-key-skip_ob button:hover { background: rgba(255, 255, 255, 0.12) !important; }
.ob-title {
    font-family: 'Montserrat', sans-serif;
    font-weight: 700;
    font-size: clamp(2.2rem, 3.4vw, 3.6rem);
    line-height: 1.2;
    color: var(--ink);
    margin: 0 0 1rem 0;
}
.ob-sub {
    font-size: clamp(1.05rem, 1.4vw, 1.5rem);
    line-height: 1.55;
    color: var(--muted);
    margin-bottom: 2rem;
}
.ob-h2 {
    font-family: 'Montserrat', sans-serif;
    font-weight: 700;
    font-size: clamp(1.4rem, 1.9vw, 2rem);
    color: var(--ink);
    margin: 2rem 0 0.8rem 0;
}

/* section cards */
[class*="st-key-card_"] {
    border: 2px solid var(--line);
    border-radius: 22px;
    padding: 1.4rem 1.6rem 1.6rem 1.6rem;
}

/* ---------- inputs ---------- */
[data-testid="stWidgetLabel"] p {
    font-size: 1.15rem !important;
    font-weight: 500;
    color: var(--ink);
}
[data-baseweb="input"],
[data-baseweb="base-input"],
[data-baseweb="textarea"],
[data-baseweb="textarea"] > div {
    background: #ffffff !important;
    border-radius: 20px !important;
}
[data-baseweb="input"],
[data-baseweb="textarea"] {
    border: 2px solid var(--line) !important;
}
[data-baseweb="input"] input {
    min-height: 3rem;
    padding: 0.4rem 1.1rem !important;
    color: var(--ink);
}
[data-baseweb="textarea"] textarea {
    padding: 1rem 1.1rem !important;
    color: var(--ink);
}
[data-baseweb="input"]:focus-within,
[data-baseweb="textarea"]:focus-within {
    border-color: var(--teal-soft, #3f8f86) !important;
}

/* ---------- chips (skills + socials) ---------- */
[class*="st-key-chips_"] { flex-wrap: wrap; gap: 0.7rem !important; margin-top: 0.4rem; }
[class*="st-key-chip_"] button {
    background: var(--chip) !important;
    border: none !important;
    border-radius: 999px !important;
    min-height: 40px;
    padding: 0.2rem 1.1rem !important;
}
[class*="st-key-chip_"] button p {
    color: #1e2a32 !important;
    font-size: 0.95rem;
    font-weight: 500;
}
[class*="st-key-chip_"] button:hover { filter: brightness(0.95); }

/* ---------- navigation buttons ---------- */
.st-key-nav_row { margin-top: 2.5rem; }
.st-key-nav_next button {
    background: var(--teal) !important;
    border: none !important;
    border-radius: 22px !important;
    min-height: 60px;
    padding: 0.5rem 2.8rem !important;
}
.st-key-nav_next button p {
    color: #ffffff !important;
    font-family: 'Montserrat', sans-serif;
    font-weight: 700;
    font-size: 1.3rem;
}
.st-key-nav_next button:hover { background: var(--teal-hover) !important; }

.st-key-nav_back button {
    background: #ffffff !important;
    border: 3px solid var(--teal-ring) !important;
    border-radius: 22px !important;
    min-height: 60px;
    padding: 0.5rem 2.6rem !important;
}
.st-key-nav_back button p {
    color: var(--teal-ring) !important;
    font-family: 'Montserrat', sans-serif;
    font-weight: 700;
    font-size: 1.3rem;
}
.st-key-nav_back button:hover { background: #effaf8 !important; }

/* ---------- ID upload ---------- */
.st-key-upload_box {
    border: 3px dashed #2b2e30;
    border-radius: 28px;
    padding: 2.5rem 2rem 2rem 2rem;
    max-width: 860px;
    margin: 1.5rem auto 0 auto;
    align-items: center;
    text-align: center;
}
.ob-upload-text {
    font-size: 1.6rem;
    color: #7d7d7d;
    line-height: 1.6;
}
.ob-upload-hint {
    text-align: center;
    color: var(--ink);
    font-size: 1.1rem;
    margin-top: 0.8rem;
}
/* turn the stock uploader into a single "Browse Computer" button */
[data-testid="stFileUploaderDropzone"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    justify-content: center;
}
[data-testid="stFileUploaderDropzoneInstructions"] { display: none !important; }
/* only the dropzone's own button (the real browse button) becomes "Browse Computer" */
[data-testid="stFileUploaderDropzone"] > button {
    background: #ffffff !important;
    border: 3px solid #3a3d3f !important;
    border-radius: 22px !important;
    padding: 0.6rem 1.6rem !important;
    min-height: 56px;
    white-space: nowrap;
}
/* hide its stock icon and label */
[data-testid="stFileUploaderDropzone"] > button > * { display: none !important; }
[data-testid="stFileUploaderDropzone"] > button::after {
    content: "Browse Computer";
    font-family: 'Montserrat', sans-serif;
    font-weight: 700;
    font-size: 1.3rem;
    color: #000000;
}
/* small screens: stack the panels */
@media (max-width: 900px) {
    .st-key-ob_left { position: static; width: 100%; height: auto; padding: 2.5rem 1.5rem; }
    .st-key-ob_right { margin-left: 0; width: 100% !important; max-width: 100% !important; padding: 2rem 1.5rem 4rem 1.5rem; }
}
</style>
"""

CLOUD_ICON = (
    '<svg width="120" height="120" viewBox="0 0 24 24" fill="none" stroke="#7d7d7d" '
    'stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M4 14.9A7 7 0 1 1 15.7 8h1.8a4.5 4.5 0 0 1 2.5 8.2"/>'
    '<path d="M12 12v9"/><path d="m16 16-4-4-4 4"/></svg>'
)


# ---------------------------------------------------------------- helpers
def _init_state():
    st.session_state.setdefault("ob_step", 1)
    st.session_state.setdefault(
        "ob_data",
        {
            "major": "",
            "bio": "",
            "skills": [],
            "portfolio": "",
            "linkedin": "",
            "github": "",
            "socials": [],
        },
    )


def _go(step: int):
    st.session_state.ob_step = step
    st.rerun()


def _add_to_list(input_key: str, data_key: str):
    """on_change callback: push the typed value into the list, then clear the box."""
    value = st.session_state.get(input_key, "").strip()
    items = st.session_state.ob_data[data_key]
    if value and value not in items:
        items.append(value)
    st.session_state[input_key] = ""


def _chips(data_key: str, prefix: str):
    """Pill-shaped buttons; clicking one removes it."""
    items = st.session_state.ob_data[data_key]
    if not items:
        return
    with st.container(horizontal=True, key=f"chips_{prefix}"):
        for i, item in enumerate(items):
            if st.button(f"{item}   ✕", key=f"chip_{prefix}_{i}"):
                items.pop(i)
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

        # TEMP (testing only): delete this block + the .st-key-skip_ob CSS before launch
        if st.button("Skip onboarding (testing)", key="skip_ob"):
            st.session_state.onboarding_complete = True
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
def _step_basic(data: dict):
    _header("Basic Information", "Tell us more about yourself and what you’re passionate about")
    st.space("small")

    data["major"] = st.text_input("Strand / Major / Degree Program", value=data["major"])
    data["bio"] = st.text_area(
        "Short Bio", value=data["bio"], height=200, max_chars=150
    )

    _, nxt = _nav(1)
    if nxt:
        _go(2)


def _step_skills(data: dict):
    _header(
        "Skills & Portfolio",
        "Add your skills and links to our work to attract potential clients or collaborators.",
    )

    st.markdown('<div class="ob-h2">Skills</div>', unsafe_allow_html=True)
    with st.container(key="card_skills"):
        st.text_input(
            "Add Skills",
            key="skill_input",
            on_change=_add_to_list,
            args=("skill_input", "skills"),
            help="Press Enter to add",
        )
        _chips("skills", "skills")

    st.markdown('<div class="ob-h2">Portfolio & Links</div>', unsafe_allow_html=True)
    with st.container(key="card_portfolio"):
        data["portfolio"] = st.text_input("Personal Portfolio", value=data["portfolio"])
        c1, c2 = st.columns(2)
        with c1:
            data["linkedin"] = st.text_input("LinkedIn", value=data["linkedin"])
        with c2:
            data["github"] = st.text_input("Github", value=data["github"])

    st.markdown('<div class="ob-h2">Professional Socials</div>', unsafe_allow_html=True)
    with st.container(key="card_socials"):
        st.text_input(
            "Add Social Media Link",
            key="social_input",
            on_change=_add_to_list,
            args=("social_input", "socials"),
            help="Press Enter to add",
        )
        _chips("socials", "socials")

    back, nxt = _nav(2)
    if back:
        _go(1)
    if nxt:
        _go(3)


def _step_id(data: dict):
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
    st.markdown(
        '<div class="ob-upload-hint">PNG or JPG, Max size is 5MB</div>',
        unsafe_allow_html=True,
    )

    if uploaded is not None and uploaded.size > 5 * 1024 * 1024:
        st.error("File is larger than 5MB. Please upload a smaller image.")

    back, nxt = _nav(3)
    if back:
        _go(2)
    if nxt:
        # TODO: validate + save the profile / ID image to your backend
        st.session_state.onboarding_complete = True
        st.rerun()


# ---------------------------------------------------------------- entry
def render_onboarding():
    _init_state()
    step = st.session_state.ob_step
    data = st.session_state.ob_data

    st.markdown(CSS, unsafe_allow_html=True)
    _left_panel(step)

    with st.container(key="ob_right"):
        if step == 1:
            _step_basic(data)
        elif step == 2:
            _step_skills(data)
        else:
            _step_id(data)


# Only run onboarding while the user hasn't finished it.
# app.py can set st.session_state.onboarding_complete = True for returning users
# (e.g. after loading `user.onboarded` from your database).
if not st.session_state.get("onboarding_complete", False):
    render_onboarding()