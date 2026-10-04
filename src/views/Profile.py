import base64

import streamlit as st

# If app.py already calls st.set_page_config, this raises and is ignored.
try:
    st.set_page_config(page_title="Profile", layout="wide")
except Exception:
    pass

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Montserrat:wght@700;800&display=swap');

:root {
    --teal: #0f6b62;
    --teal-hover: #0b5750;
    --teal-soft: #3f8f86;
    --mint: #4ccfc0;
    --ink: #3a3d3f;
    --muted: #5b6770;
    --line: #dcdfe2;
    --field: #e8edf1;
    --chip: #9fd9f5;
    --danger: #ff3131;
    --danger-btn: #e32626;
    --danger-bg: #fde4e4;
}

/* ---------- main area (same frame as Marketplace) ---------- */
[data-testid="stMain"] { background: #ffffff; color: var(--ink); }
[data-testid="stMain"] p,
[data-testid="stMain"] button,
[data-testid="stMain"] input,
[data-testid="stMain"] textarea,
[data-testid="stDialog"] p,
[data-testid="stDialog"] button,
[data-testid="stDialog"] input { font-family: 'Inter', sans-serif; }
[data-testid="stMain"] h1 { font-family: 'Montserrat', sans-serif; font-weight: 800; color: var(--ink); padding-bottom: 0; }
[data-testid="stMain"] h2, [data-testid="stMain"] h3 { color: var(--ink); }
[data-testid="stDialog"] h2 { font-family: 'Montserrat', sans-serif; font-weight: 700; color: var(--ink); }

[data-testid="stMainBlockContainer"] { padding-top: 2rem !important; padding-bottom: 3rem !important; }
[data-testid="stMainBlockContainer"], .block-container {
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    max-width: 100% !important;
}

.pf-h2 { font-family: 'Montserrat', sans-serif; font-weight: 700; font-size: 1.5rem; color: var(--ink); line-height: 1.2; margin: 0; }
.pf-h2.danger { color: var(--danger); }

/* ---------- tabs ---------- */
[data-baseweb="tab-list"] { gap: 0; width: max-content; }
button[data-baseweb="tab"] { min-width: 11rem; justify-content: center; padding: 0.6rem 1rem; }
button[data-baseweb="tab"] p { font-family: 'Montserrat', sans-serif; font-weight: 700; font-size: 1rem; color: var(--muted); }
button[data-baseweb="tab"][aria-selected="true"] p { color: var(--teal-soft); }
[data-baseweb="tab-highlight"] { background: var(--teal) !important; height: 3px !important; }
[data-baseweb="tab-border"] { background: var(--line) !important; height: 3px !important; }

/* ---------- banner ---------- */
.st-key-banner { background: var(--field); border-radius: 18px; padding: 1.3rem 2rem 2.5rem 2rem; margin-top: 0.5rem; }
.st-key-avatar { position: relative; width: 128px !important; min-width: 128px !important; max-width: 128px !important; height: 128px; flex: 0 0 128px !important; margin-right: 0 !important; }
.pf-avatar { width: 128px; height: 128px; border-radius: 50%; border: 3px solid var(--mint); background: #f3f6f8 center/cover no-repeat; box-sizing: border-box; }
.st-key-cam_btn { position: absolute !important; right: 0 !important; bottom: 0 !important; left: auto !important; top: auto !important; width: 38px !important; height: 38px !important; margin: 0 !important; z-index: 2; }
.st-key-cam_btn [data-testid="stButton"] { width: 38px; margin: 0; }
.st-key-cam_btn button { width: 38px; height: 38px; min-height: 0; padding: 0 !important; display: flex; align-items: center; justify-content: center; border-radius: 50% !important; background: #ffffff !important; border: 2px solid #111 !important; }
.st-key-cam_btn button p { display: none; }
.st-key-cam_btn button span { font-size: 1.1rem !important; color: #111 !important; }
.pf-name { font-family: 'Montserrat', sans-serif; font-weight: 800; font-size: 1.9rem; line-height: 1.2; color: var(--ink); }
.pf-major { font-size: 1rem; color: var(--ink); }
.pf-rating { font-size: 0.9rem; color: var(--muted); margin-top: 0.3rem; }
.pf-rating .star { color: #fbc02d; margin-right: 0.4rem; }
.st-key-banner_row > [data-testid="stLayoutWrapper"]:has(.st-key-avatar) {
    flex: 0 0 128px !important;
    width: 128px !important;
    min-width: 128px !important;
}
.st-key-banner_row > [data-testid="stLayoutWrapper"]:has(.st-key-banner_info) {
    flex: 1 1 0 !important;
    width: auto !important;
    min-width: 0;
}
.st-key-banner_row { gap: 3rem !important; }
/* ---------- pencil buttons ---------- */
[class*="st-key-edit_"] { width: auto !important; flex: 0 0 auto; }
[class*="st-key-edit_"] button { min-height: 0; padding: 0.1rem 0.3rem !important; background: transparent !important; border: none !important; box-shadow: none !important; }
[class*="st-key-edit_"] button span { font-size: 1.1rem !important; color: var(--ink) !important; }
[class*="st-key-edit_"] button:hover { background: rgba(0, 0, 0, 0.06) !important; }

/* ---------- section cards (same look as listing cards) ---------- */
[class*="st-key-card_"] { background: #ffffff; border-radius: 18px; padding: 1rem 1.2rem 1.3rem 1.2rem !important; box-shadow: 0 2px 12px rgba(27, 42, 65, 0.14); gap: 0.5rem; }
.st-key-card_skills, .st-key-card_socials { padding-bottom: 0.5rem !important; }
.st-key-card_about { padding-bottom: 2rem !important; }
.st-key-card_portfolio { padding-bottom: 1.8rem !important; }
.pf-about { font-size: 0.9rem; line-height: 1.5; color: var(--ink); white-space: pre-wrap; }
.pf-chip { display: inline-block; background: var(--field); border-radius: 999px; padding: 0.3rem 0.9rem; margin: 0 0.5rem 0.5rem 0; font-weight: 500; font-size: 0.8rem; color: var(--ink); }
.pf-chip.wide { padding: 0.4rem 1.3rem; }
.pf-label { font-weight: 600; font-size: 0.8rem; color: var(--ink); margin: 0 0 0.3rem 0.3rem; }
.pf-pill { background: var(--field); border-radius: 999px; padding: 0.5rem 1rem; text-align: center; font-size: 0.85rem; word-break: break-all; min-height: 2.2rem; }

/* ---------- inputs ---------- */
[data-testid="stMain"] [data-testid="stWidgetLabel"] p,
[data-testid="stDialog"] [data-testid="stWidgetLabel"] p { font-size: 0.85rem !important; font-weight: 600; color: var(--ink); }
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="textarea"], [data-baseweb="textarea"] > div { background: var(--field) !important; border-radius: 14px !important; }
[data-baseweb="input"], [data-baseweb="textarea"] { border: 1.5px solid transparent !important; }
[data-baseweb="input"] input { padding: 0.3rem 1rem !important; color: var(--ink); font-size: 0.9rem; }
[data-baseweb="textarea"] textarea { padding: 0.8rem 1rem !important; color: var(--ink); font-size: 0.9rem; }
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within { border-color: var(--teal-soft) !important; }

/* ---------- chips inside dialogs ---------- */
[class*="st-key-chips_"] { flex-wrap: wrap; gap: 0.5rem !important; margin-top: 0.3rem; }
[class*="st-key-chip_"] button { background: var(--chip) !important; border: none !important; border-radius: 999px !important; min-height: 1.9rem; padding: 0.1rem 0.9rem !important; }
[class*="st-key-chip_"] button p { color: #1e2a32 !important; font-size: 0.8rem; font-weight: 500; }
[class*="st-key-chip_"] button:hover { filter: brightness(0.95); }

/* ---------- action buttons: teal pills like "Add a Listing" ---------- */
.st-key-pw_confirm button, .st-key-dlg_save button, .st-key-pw_yes button, .st-key-photo_save button, [class*="st-key-save_"] button {
    background: var(--teal) !important; border: none !important; border-radius: 999px !important; min-height: 1.9rem; padding: 0 1.3rem !important; white-space: nowrap; }
.st-key-pw_confirm button p, .st-key-dlg_save button p, .st-key-pw_yes button p, .st-key-photo_save button p, [class*="st-key-save_"] button p { color: #ffffff !important; font-weight: 600; font-size: 0.85rem; }
.st-key-pw_confirm button:hover, .st-key-dlg_save button:hover, .st-key-pw_yes button:hover, .st-key-photo_save button:hover, [class*="st-key-save_"] button:hover { background: var(--teal-hover) !important; }
.st-key-dlg_save button:disabled, .st-key-photo_save button:disabled { opacity: 0.4; }

.st-key-dlg_cancel button, .st-key-pw_no button, .st-key-del_no button, .st-key-photo_cancel button {
    background: #ffffff !important; border: 1.5px solid var(--teal) !important; border-radius: 999px !important; min-height: 1.9rem; padding: 0 1.3rem !important; }
.st-key-dlg_cancel button p, .st-key-pw_no button p, .st-key-del_no button p, .st-key-photo_cancel button p { color: var(--teal) !important; font-weight: 600; font-size: 0.85rem; }
.st-key-dlg_cancel button:hover, .st-key-pw_no button:hover, .st-key-del_no button:hover, .st-key-photo_cancel button:hover { background: #effaf8 !important; }

/* ---------- danger zone ---------- */
.st-key-card_danger { background: var(--danger-bg); border-top: 4px solid var(--danger); box-shadow: 0 2px 12px rgba(255, 49, 49, 0.12); margin-top: 0.6rem; padding: 1.1rem 1.2rem !important; }
.st-key-card_danger [data-testid="stHorizontalBlock"] { align-items: center !important; }
.st-key-card_danger [data-testid="stElementContainer"],
.st-key-card_danger [data-testid="stMarkdown"],
.st-key-card_danger [data-testid="stMarkdownContainer"],
.st-key-card_danger [data-testid="stMarkdownContainer"] p { margin: 0 !important; padding: 0 !important; min-height: 0; }
.st-key-card_danger .stButton { margin: 0; }
.pf-danger-title { font-weight: 700; font-size: 1rem; color: var(--ink); }
.pf-danger-sub { font-size: 0.8rem; color: var(--ink); }
.st-key-delete_btn button, .st-key-del_yes button { background: var(--danger-btn) !important; border: none !important; border-radius: 999px !important; min-height: 1.9rem; padding: 0 1.3rem !important; }
.st-key-delete_btn button p, .st-key-del_yes button p { color: #ffffff !important; font-weight: 600; font-size: 0.85rem; }
.st-key-delete_btn button:hover, .st-key-del_yes button:hover { background: #bd1c1c !important; }
.st-key-del_yes button:disabled { opacity: 0.4; }

/* ---------- listings (same card as Marketplace) ---------- */
.pf-listing { background: #fff; border-radius: 18px; padding: 0.7rem 0.7rem 1.2rem 0.7rem; box-shadow: 0 2px 12px rgba(27, 42, 65, 0.14); }
.pf-thumb { position: relative; height: 150px; border-radius: 14px; overflow: hidden;
    background:
      radial-gradient(ellipse 55% 38% at 22% 108%, #c5dc7a 0 98%, transparent 100%),
      radial-gradient(ellipse 75% 45% at 72% 112%, #8aa300 0 98%, transparent 100%),
      linear-gradient(#bee3fa, #e8f5fd); }
.pf-price { position: absolute; top: 10px; right: 10px; background: #fff; border-radius: 999px; padding: 2px 12px; font-size: 0.75rem; font-weight: 600; color: var(--ink); }
.pf-listing-name { font-family: 'Montserrat', sans-serif; font-weight: 700; font-size: 1rem; line-height: 1.3; color: var(--ink); margin-top: 1rem; }
.pf-review { background: #fff; border-radius: 18px; padding: 1rem 1.2rem; box-shadow: 0 2px 12px rgba(27, 42, 65, 0.14); margin-bottom: 0.8rem; font-size: 0.9rem; line-height: 1.5; color: var(--ink); }
</style>
"""

DEFAULTS = {
    "username": "Username",
    "major": "Bachelor of Computer Science",
    "bio": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 6,
    "skills": ["Figma", "Python", "Tutoring"],
    "portfolio": "",
    "linkedin": "",
    "github": "",
    "socials": ["stdnt@hive.com"],
    "photo": None,  # (bytes, mime)
}


# ------------------------------------------------------------ state helpers
def _init():
    st.session_state.setdefault("profile", dict(DEFAULTS))
    st.session_state.setdefault("editing", set())
    st.session_state.setdefault("pw_round", 0)


def _p():
    return st.session_state.profile


def _start_edit(name: str):
    st.session_state.editing.add(name)


def _save_field(field: str, input_key: str, edit_name: str):
    """on_change: Enter (or leaving the box) saves the value and closes the editor."""
    _p()[field] = st.session_state[input_key].strip()
    st.session_state.editing.discard(edit_name)
    # TODO: persist to your backend here


def _save_group(edit_name: str, fields: dict):
    """Save several inputs at once; fields = {profile_key: input_key}."""
    for field, input_key in fields.items():
        _p()[field] = st.session_state[input_key].strip()
    st.session_state.editing.discard(edit_name)


def _pencil(name: str):
    st.button("", key=f"edit_{name}", icon=":material/edit:", on_click=_start_edit, args=(name,))


def _heading(text: str, name: str | None = None, cls: str = ""):
    with st.container(horizontal=True, vertical_alignment="center", key=f"hd_{name or text}"):
        st.markdown(f'<div class="pf-h2 {cls}">{text}</div>', unsafe_allow_html=True)
        if name:
            _pencil(name)


# ------------------------------------------------------------ dialogs
def _add_to_draft(input_key: str, draft_key: str):
    """Comma-separated entries are all added at once, then the box clears."""
    raw = st.session_state.get(input_key, "")
    draft = st.session_state[draft_key]
    for value in (v.strip() for v in raw.split(",")):
        if value and value not in draft:
            draft.append(value)
    st.session_state[input_key] = ""


def _list_editor(data_key: str, label: str, prefix: str):
    draft_key = f"draft_{prefix}"
    input_key = f"dlg_input_{prefix}"
    draft = st.session_state[draft_key]

    st.text_input(
        label,
        key=input_key,
        on_change=_add_to_draft,
        args=(input_key, draft_key),
        help="Press Enter to add. Separate with commas to add several at once.",
    )
    if draft:
        with st.container(horizontal=True, key=f"chips_{prefix}"):
            for i, item in enumerate(draft):
                if st.button(f"{item}   ✕", key=f"chip_{prefix}_{i}"):
                    draft.pop(i)
                    st.rerun(scope="fragment")  # keep the dialog open

    st.space("small")
    with st.container(horizontal=True, horizontal_alignment="distribute"):
        if st.button("Cancel", key="dlg_cancel"):
            st.rerun()
        if st.button("Save", key="dlg_save"):
            _p()[data_key] = list(draft)
            # TODO: persist to your backend here
            st.rerun()


@st.dialog("Edit skills", width="large")
def skills_dialog():
    _list_editor("skills", "Add skills", "skills")


@st.dialog("Edit social media links", width="large")
def socials_dialog():
    _list_editor("socials", "Add social media link", "socials")


@st.dialog("Change profile photo")
def photo_dialog():
    file = st.file_uploader("Choose an image", type=["png", "jpg", "jpeg"], key="photo_upload")
    if file is not None and file.size > 5 * 1024 * 1024:
        st.error("File is larger than 5MB. Please choose a smaller image.")
        file = None
    if file is not None:
        st.image(file, width=160)
    with st.container(horizontal=True, horizontal_alignment="distribute"):
        if st.button("Cancel", key="photo_cancel"):
            st.rerun()
        if st.button("Save photo", key="photo_save", disabled=file is None):
            _p()["photo"] = (file.getvalue(), file.type)
            # TODO: upload to storage
            st.rerun()


@st.dialog("Change password?")
def confirm_password_dialog(new_password: str):
    st.write("You’ll use your new password the next time you sign in.")
    with st.container(horizontal=True, horizontal_alignment="distribute"):
        if st.button("Cancel", key="pw_no"):
            st.rerun()
        if st.button("Yes, change it", key="pw_yes"):
            # TODO: verify the current password and update it in your backend
            st.session_state.pw_round += 1  # resets the three fields
            st.session_state.toast = "Password updated"
            st.rerun()


@st.dialog("Delete your account?")
def confirm_delete_dialog():
    st.write(
        "This permanently deletes your profile, listings, and reviews. "
        "This can’t be undone."
    )
    typed = st.text_input("Type DELETE to confirm", key="del_confirm_text")
    with st.container(horizontal=True, horizontal_alignment="distribute"):
        if st.button("Cancel", key="del_no"):
            st.rerun()
        if st.button("Delete account", key="del_yes", disabled=typed.strip() != "DELETE"):
            # TODO: delete the user in your backend, clear the session, send to login
            st.session_state.toast = "Account deleted"
            st.rerun()


# ------------------------------------------------------------ summary tab
def _inline_text(field: str, edit_name: str, display_cls: str):
    """Text that turns into a text box when its pencil is clicked."""
    with st.container(horizontal=True, vertical_alignment="center", key=f"row_{edit_name}"):
        if edit_name in st.session_state.editing:
            key = f"in_{edit_name}"
            st.text_input(
                field, value=_p()[field], key=key, label_visibility="collapsed",
                on_change=_save_field, args=(field, key, edit_name),
            )
        else:
            st.markdown(f'<div class="{display_cls}">{_p()[field]}</div>', unsafe_allow_html=True)
            _pencil(edit_name)


def _banner():
    p = _p()
    if p["photo"]:
        data, mime = p["photo"]
        style = f"background-image:url(data:{mime};base64,{base64.b64encode(data).decode()})"
    else:
        style = ""

    with st.container(key="banner"):
        with st.container(horizontal=True, vertical_alignment="center", key="banner_row"):
            with st.container(key="avatar"):
                st.markdown(f'<div class="pf-avatar" style="{style}"></div>', unsafe_allow_html=True)
                if st.button("", key="cam_btn", icon=":material/photo_camera:"):
                    photo_dialog()
            with st.container(key="banner_info"):
                _inline_text("username", "username", "pf-name")
                _inline_text("major", "major", "pf-major")
                st.markdown('<div class="pf-rating"><span class="star">★</span>4.8 (124 reviews)</div>', unsafe_allow_html=True)

def _about():
    _heading("About me", "about")
    with st.container(key="card_about"):
        if "about" in st.session_state.editing:
            st.text_area(
                "Short bio", value=_p()["bio"], key="in_about", height=200, max_chars=500,
                label_visibility="collapsed", help="Press Ctrl+Enter to save",
            )
            with st.container(horizontal=True, horizontal_alignment="right"):
                st.button("Save", key="save_about", on_click=_save_group, args=("about", {"bio": "in_about"}))
        else:
            st.markdown(f'<div class="pf-about">{_p()["bio"]}</div>', unsafe_allow_html=True)


def _chip_html(items, wide=False):
    if not items:
        return '<div class="pf-about" style="color:#8a949c">Nothing added yet.</div>'
    cls = "pf-chip wide" if wide else "pf-chip"
    return "".join(f'<span class="{cls}">{i}</span>' for i in items)


def _skills():
    with st.container(horizontal=True, vertical_alignment="center", key="hd_skills"):
        st.markdown('<div class="pf-h2">Skills</div>', unsafe_allow_html=True)
        if st.button("", key="edit_skills", icon=":material/edit:"):
            st.session_state.draft_skills = list(_p()["skills"])
            skills_dialog()
    with st.container(key="card_skills"):
        st.markdown(_chip_html(_p()["skills"]), unsafe_allow_html=True)


def _portfolio():
    p = _p()
    _heading("Portfolio & Links", "portfolio")
    with st.container(key="card_portfolio"):
        if "portfolio" in st.session_state.editing:
            st.text_input("Personal Portfolio", value=p["portfolio"], key="in_portfolio")
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("LinkedIn", value=p["linkedin"], key="in_linkedin")
            with c2:
                st.text_input("Github", value=p["github"], key="in_github")
            with st.container(horizontal=True, horizontal_alignment="right"):
                st.button(
                    "Save", key="save_portfolio", on_click=_save_group,
                    args=("portfolio", {"portfolio": "in_portfolio", "linkedin": "in_linkedin", "github": "in_github"}),
                )
        else:
            st.markdown('<div class="pf-label">Personal Portfolio</div>'
                        f'<div class="pf-pill">{p["portfolio"] or "&nbsp;"}</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            c1.markdown('<div class="pf-label" style="margin-top:1rem">LinkedIn</div>'
                        f'<div class="pf-pill">{p["linkedin"] or "&nbsp;"}</div>', unsafe_allow_html=True)
            c2.markdown('<div class="pf-label" style="margin-top:1rem">Github</div>'
                        f'<div class="pf-pill">{p["github"] or "&nbsp;"}</div>', unsafe_allow_html=True)


def _socials():
    with st.container(horizontal=True, vertical_alignment="center", key="hd_socials"):
        st.markdown('<div class="pf-h2">Social Media Accounts</div>', unsafe_allow_html=True)
        if st.button("", key="edit_socials", icon=":material/edit:"):
            st.session_state.draft_socials = list(_p()["socials"])
            socials_dialog()
    with st.container(key="card_socials"):
        st.markdown(_chip_html(_p()["socials"], wide=True), unsafe_allow_html=True)


def _listings():
    t1, t2 = st.tabs(["Active Listing", "Reviews"])
    with t1:
        cols = st.columns(4)
        for col in cols:
            col.markdown(
                '<div class="pf-listing"><div class="pf-thumb"><span class="pf-price">20/hr</span></div>'
                '<div class="pf-listing-name">Tutoring Something idk</div></div>',
                unsafe_allow_html=True,
            )
    with t2:
        for who, text in [("Student A", "Clear explanations and always on time."),
                          ("Student B", "Helped me finally understand recursion.")]:
            st.markdown(f'<div class="pf-review"><b>{who}</b> · ★ 5.0<br>{text}</div>', unsafe_allow_html=True)


def _summary_tab():
    # Row 1: profile banner on the left, About me on the right
    banner_col, about_col = st.columns([1.5, 1.3])
    with banner_col:
        _banner()
    with about_col:
        _about()

    # Row 2: Portfolio & Links and Social Media share most of the width, Skills on the right
    portfolio_col, socials_col, skills_col = st.columns([1.5, 1.5, 1])
    with portfolio_col:
        _portfolio()
    with socials_col:
        _socials()
    with skills_col:
        _skills()

    _listings()

# ------------------------------------------------------------ settings tab
def _settings_tab():
    st.space("small")
    left, right = st.columns([1.1, 1], gap="large")
    n = st.session_state.pw_round

    with left:
        _heading("Change Password")
        with st.container(key="card_password"):
            cur = st.text_input("Enter Current Password", type="password", key=f"pw_cur_{n}")
            new = st.text_input("Enter New Password", type="password", key=f"pw_new_{n}")
            ver = st.text_input("Verify New Password", type="password", key=f"pw_ver_{n}")
            error = None
            with st.container(horizontal=True, horizontal_alignment="center"):
                clicked = st.button("Confirm", key="pw_confirm")
            if clicked:
                if not (cur and new and ver):
                    error = "Fill in all three password fields."
                elif len(new) < 8:
                    error = "New password must be at least 8 characters."
                elif new != ver:
                    error = "New passwords don’t match."
                elif new == cur:
                    error = "New password must be different from your current one."
                if error:
                    st.error(error)
                else:
                    confirm_password_dialog(new)

    with right:
        _heading("Danger Zone", cls="danger")
        with st.container(key="card_danger"):
            with st.container(horizontal=True, vertical_alignment="center", horizontal_alignment="distribute"):
                st.markdown('<div><div class="pf-danger-title">Delete Account</div>'
                            '<div class="pf-danger-sub">Permanently Delete All Account Information</div></div>',
                            unsafe_allow_html=True)
                if st.button("Delete", key="delete_btn"):
                    confirm_delete_dialog()


# ------------------------------------------------------------ entry
def render_profile():
    _init()
    st.markdown(CSS, unsafe_allow_html=True)

    if "toast" in st.session_state:
        st.toast(st.session_state.pop("toast"))

    st.title("Profile Information")
    st.caption("Keep your profile up to date to build trust with other students")
    
    summary, settings = st.tabs(["Summary", "Settings"])
    with summary:
        _summary_tab()
    with settings:
        _settings_tab()


render_profile()