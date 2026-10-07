"""Create a Listing: 4-step wizard shown inside the Marketplace page.

Flow:  1. Type (Gig / Rental)  ->  1b. Deliverable type (Gigs only)
       2. Details  ->  3. Upload Images  ->  4. Review and Post

Colors and fonts (--teal, --orange, --ink, --muted, Montserrat, Inter) come
from the style block at the top of Marketplace.py.
"""
from html import escape

import streamlit as st

from models.listing import MAX_IMAGES, RATE_TYPES, RATE_UNITS
from views.session import get_listing_controller

# ==========================================
# STYLES (Create a Listing page only)
# ==========================================

WIZARD_CSS = """
:root {
    --wiz-line: #c5ced6;
    --wiz-gray: #c9d0d8;
    --wiz-teal: #0b9488;
    --wiz-btn: #e8edf1;
}

/* ---------- page heading ---------- */
.sh-wiz-title {
    font-family: 'Montserrat', sans-serif;
    font-weight: 800;
    font-size: 2.4rem;
    line-height: 1.2;
    color: var(--ink);
}
.sh-wiz-sub {
    font-family: 'Inter', sans-serif;
    font-size: 1.25rem;
    color: var(--muted);
    margin: 0.2rem 0 1.4rem;
}

/* ---------- progress card (left) ---------- */
.sh-wiz-progress {
    border: 1px solid var(--wiz-line);
    border-radius: 30px;
    padding: 1.9rem 1.8rem 1.7rem;
}
.sh-wiz-ptitle {
    font-family: 'Montserrat', sans-serif;
    font-weight: 800;
    font-size: 1.05rem;
    color: var(--ink);
    margin-bottom: 0.8rem;
}
.sh-wiz-step {
    position: relative;
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.9rem;
}
.sh-wiz-step:last-child { margin-bottom: 0; }
.sh-wiz-step .num {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    background: var(--wiz-gray);
    color: var(--ink);
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Montserrat', sans-serif;
    font-weight: 800;
    font-size: 1.2rem;
    flex-shrink: 0;
}
.sh-wiz-step.active .num { background: var(--wiz-teal); color: #ffffff; }
.sh-wiz-step .lbl { font-family: 'Inter', sans-serif; font-size: 0.8rem; color: var(--muted); }
/* connector line between the circles */
.sh-wiz-step:not(:last-child)::after {
    content: "";
    position: absolute;
    left: 18px;
    top: 38px;
    width: 2px;
    height: 0.9rem;
    background: #4a4f55;
}

/* ---------- main card (right) ---------- */
.st-key-wiz_card {
    border: 1px solid var(--wiz-line);
    border-radius: 40px;
    padding: 2.6rem 2.6rem 2rem !important;
    min-height: 29rem;
    gap: 0.6rem;
}
.sh-wiz-h {
    font-family: 'Montserrat', sans-serif;
    font-weight: 800;
    font-size: 1.7rem;
    line-height: 1.2;
    color: var(--ink);
}
.sh-wiz-cap {
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    color: var(--muted);
    margin-top: 0.15rem;
}
/* Streamlit gives markdown a -1rem bottom margin; remove it so the heading,
   caption and the content below keep a normal gap */
.st-key-wiz_card [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }

/* ---------- selectable choice cards ----------
   The visible card is HTML. The wrapper of the (invisible) button
   (st-key-pick_*) is stretched over the whole card, so a click anywhere
   on the card selects it. */
[class*="st-key-choice_"] { position: relative; gap: 0; }
/* Streamlit gives markdown a -1rem bottom margin, which would make the card
   taller than its clickable area; remove it so both are exactly the same size */
[class*="st-key-choice_"] [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }
[class*="st-key-pick_"] {
    position: absolute !important;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    width: 100% !important;
    height: 100% !important;
    margin: 0 !important;
    z-index: 5;
}
[class*="st-key-pick_"] [data-testid="stButton"],
[class*="st-key-pick_"] button {
    position: static;
    width: 100% !important;
    height: 100% !important;
    min-height: 0;
    opacity: 0;
    cursor: pointer;
}
.sh-choice {
    border: 1px solid var(--wiz-line);
    border-radius: 22px;
    padding: 1.7rem 1rem 1.5rem;
    text-align: center;
    background: #ffffff;
    transition: border-color 0.15s, box-shadow 0.15s;
}
[class*="st-key-choice_"]:hover .sh-choice { border-color: var(--wiz-teal); }
.sh-choice.selected {
    border-color: var(--wiz-teal);
    box-shadow: 0 0 0 2px var(--wiz-teal);
}
.sh-choice .ico {
    width: 7rem;
    height: 7rem;
    border-radius: 50%;
    background: var(--wiz-gray);
    margin: 0 auto 1.1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 3.2rem;
}
.sh-choice .ttl {
    font-family: 'Montserrat', sans-serif;
    font-weight: 700;
    font-size: 1.1rem;
    color: var(--ink);
}
.sh-choice .sub {
    font-family: 'Inter', sans-serif;
    font-size: 1rem;
    color: #4b5560;
    margin-top: 0.35rem;
}

/* ---------- form fields (pill inputs) ---------- */
.st-key-wiz_card [data-testid="stWidgetLabel"] p {
    font-size: 0.85rem;
    color: var(--muted);
    margin-bottom: 0;
}
/* single-line fields: pill shape, light border (new Streamlit markup first,
   older data-baseweb markup as a fallback) */
.st-key-wiz_card [data-testid="stTextInputRootElement"],
.st-key-wiz_card [data-testid="stNumberInputContainer"],
.st-key-wiz_card [data-testid="stSelectbox"] > div > div,
.st-key-wiz_card [data-testid="stTextInput"] [data-baseweb="input"],
.st-key-wiz_card [data-testid="stNumberInput"] [data-baseweb="input"],
.st-key-wiz_card [data-testid="stSelectbox"] [data-baseweb="select"] > div {
    border: 1px solid var(--wiz-line) !important;
    border-radius: 999px !important;
    background: #ffffff !important;
    padding-left: 0.4rem;
}
/* description box: rounded rectangle */
.st-key-wiz_card [data-testid="stTextAreaRootElement"],
.st-key-wiz_card [data-testid="stTextArea"] [data-baseweb="textarea"] {
    border: 1px solid var(--wiz-line) !important;
    border-radius: 22px !important;
    background: #ffffff !important;
}
/* teal focus instead of Streamlit's default red */
.st-key-wiz_card [data-testid="stTextInputRootElement"]:focus-within,
.st-key-wiz_card [data-testid="stNumberInputContainer"]:focus-within,
.st-key-wiz_card [data-testid="stSelectbox"] > div > div:focus-within,
.st-key-wiz_card [data-testid="stTextAreaRootElement"]:focus-within {
    border-color: var(--wiz-teal) !important;
    box-shadow: 0 0 0 1px var(--wiz-teal) !important;
}
.st-key-wiz_card [data-testid="stFileUploaderDropzone"] {
    border: 1px solid var(--wiz-line);
    border-radius: 22px;
    background: #ffffff;
    min-height: 14rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.6rem;
}

/* small preview of the chosen images under the dropzone */
.st-key-wiz_card [data-testid="stImage"] { gap: 0.5rem; flex-wrap: wrap; }

/* ---------- review rows ---------- */
.sh-wiz-typerow {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: 0.95rem;
    color: var(--muted);
    margin-bottom: 0.3rem;
}
.sh-wiz-pill {
    background: var(--wiz-teal);
    color: #ffffff;
    font-weight: 700;
    font-size: 0.8rem;
    padding: 0.25rem 1.1rem;
    border-radius: 999px;
}
.sh-wiz-pill.rental { background: var(--orange); }
.sh-wiz-chip {
    background: var(--wiz-btn);
    color: var(--ink);
    font-weight: 600;
    font-size: 0.75rem;
    padding: 0.25rem 0.9rem;
    border-radius: 999px;
}
.sh-wiz-label { font-size: 0.85rem; color: var(--muted); margin-top: 0.4rem; }
.sh-wiz-value {
    border: 1px solid var(--wiz-line);
    border-radius: 999px;
    padding: 0.5rem 1rem;
    min-height: 2.3rem;
    display: flex;
    align-items: center;
    font-size: 0.9rem;
    color: var(--ink);
}
.sh-wiz-value.multi { border-radius: 22px; white-space: pre-wrap; align-items: flex-start; }

/* ---------- Go Back / Next Step / Post buttons ---------- */
.st-key-wiz_nav { margin-top: 1rem; }
.st-key-wiz_next,
.st-key-wiz_post {
    display: flex;
    justify-content: flex-end;     /* Next Step / Post sit on the right */
    width: 100% !important;        /* Streamlit sizes the wrapper to fit-content */
}
.st-key-wiz_next [data-testid="stButton"],
.st-key-wiz_post [data-testid="stButton"] {
    width: fit-content !important; /* ...but the button itself stays compact */
    flex: 0 0 auto;
}
.st-key-wiz_back button,
.st-key-wiz_clear button,
.st-key-wiz_next button,
.st-key-wiz_post button {
    border: none;
    border-radius: 8px;
    min-height: 2.1rem;
    min-width: 7.5rem;
}
.st-key-wiz_back button,
.st-key-wiz_clear button,
.st-key-wiz_next button { background: var(--wiz-btn); }
.st-key-wiz_back button p,
.st-key-wiz_clear button p,
.st-key-wiz_next button p { color: #1b1b1b; font-weight: 700; font-size: 0.8rem; }
.st-key-wiz_back button:hover,
.st-key-wiz_clear button:hover,
.st-key-wiz_next button:hover { background: #dbe3e9; border: none; }
.st-key-wiz_post button { background: var(--wiz-teal); }
.st-key-wiz_post button p { color: #ffffff; font-weight: 700; font-size: 0.8rem; }
.st-key-wiz_post button:hover { background: var(--teal-hover); border: none; }
"""

# ==========================================
# WIZARD STATE
# ==========================================

STEP_NUMBER = {"type": 1, "deliverable": 1, "details": 2, "media": 3, "review": 4}
PROGRESS_LABELS = ["Type of Listing", "Details", "Upload Images", "Review and Post"]


def _new_state() -> dict:
    return {
        "step": "type",            # type | deliverable | details | media | review
        "category": None,          # "Gig" or "Rental"
        "deliverable": None,       # Gigs only
        "title": "",
        "rate_type": "Hourly Rate",
        "rate": 100.0,
        "description": "",
        "images": [],              # [{"bytes": ..., "name": ..., "mime": ...}, ...]
    }


def reset_wizard() -> None:
    """Start a fresh wizard (called when 'Add a Listing' is clicked)."""
    st.session_state.wiz = _new_state()


def _exit() -> None:
    st.session_state.creating_listing = False
    reset_wizard()


def _pick_category(value: str) -> None:
    w = st.session_state.wiz
    if w["category"] != value:
        w["category"] = value
        w["deliverable"] = None
        w["rate_type"] = "Hourly Rate" if value == "Gig" else "Daily Rate"


def _pick_deliverable(value: str) -> None:
    st.session_state.wiz["deliverable"] = value


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


# ==========================================
# SCREENS
# ==========================================

def _screen_type(w: dict, market) -> None:
    _heading("What are you listing?", "Choose what type of service are you offering.")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        _choice("gig", "\U0001F91D", "Offer a Gig", "Tutoring, design, etc.",
                w["category"] == "Gig", _pick_category, "Gig")
    with c2:
        _choice("rental", "\U0001F4C5", "Offer a Rental", "Camera, Books, etc.",
                w["category"] == "Rental", _pick_category, "Rental")

    _, nxt = _nav(show_back=False)   # first step: no Go Back
    if nxt:
        if not w["category"]:
            st.error("Please choose Gig or Rental to continue.")
        else:
            # the deliverable question only applies to Gigs
            w["step"] = "deliverable" if w["category"] == "Gig" else "details"
            st.rerun()


def _screen_deliverable(w: dict, market) -> None:
    _heading("What are you listing?", "Choose what type of service are you offering.")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        _choice("service", "\U0001F6CE\uFE0F", "Service Deliverables", "Tutoring etc.",
                w["deliverable"] == "Service Deliverables", _pick_deliverable,
                "Service Deliverables")
    with c2:
        _choice("project", "\U0001F4CB", "Project Deliverables", "Logo Making etc.",
                w["deliverable"] == "Project Deliverables", _pick_deliverable,
                "Project Deliverables")

    back, nxt = _nav()
    if back:
        w["step"] = "type"
        st.rerun()
    if nxt:
        if not w["deliverable"]:
            st.error("Please choose a deliverable type to continue.")
        else:
            w["step"] = "details"
            st.rerun()


def _screen_details(w: dict, market) -> None:
    noun = "services" if w["category"] == "Gig" else "item"
    _heading("Details")

    title = st.text_input("Title", value=w["title"], key="wiz_title")
    rate_types = list(RATE_UNITS)
    rate_type = st.selectbox("Rate Type", rate_types,
                             index=rate_types.index(w["rate_type"]), key="wiz_rate_type")
    rate = st.number_input("Rate (\u20b1)", min_value=0.0, step=50.0,
                           value=float(w["rate"]), key="wiz_rate")
    description = st.text_area(f"Add a description of your {noun}",
                               value=w["description"], height=110, key="wiz_desc")

    def save() -> None:
        w.update(title=title, rate_type=rate_type, rate=rate, description=description)

    back, nxt = _nav()
    if back:
        save()
        w["step"] = "deliverable" if w["category"] == "Gig" else "type"
        st.rerun()
    if nxt:
        save()
        if not title.strip():
            st.error("Please add a title.")
        elif rate <= 0:
            st.error("Please enter a rate greater than 0.")
        else:
            w["step"] = "media"
            st.rerun()


def _screen_media(w: dict, market) -> None:
    noun = "services" if w["category"] == "Gig" else "item"
    _heading("Upload Images", f"Upload up to {MAX_IMAGES} images of your {noun}")

    files = st.file_uploader("Upload images", type=["png", "jpg", "jpeg", "webp"],
                             accept_multiple_files=True, key="wiz_files",
                             label_visibility="collapsed")
    if len(files) > MAX_IMAGES:
        st.warning(f"You can add up to {MAX_IMAGES} images, so only the first "
                   f"{MAX_IMAGES} will be used.")
        files = files[:MAX_IMAGES]

    def chosen() -> list:
        """New uploads replace the saved images; otherwise keep what was saved."""
        if files:
            return [{"bytes": f.getvalue(), "name": f.name, "mime": f.type or "image/png"}
                    for f in files]
        return w["images"]

    shown = chosen()
    if shown:
        st.image([img["bytes"] for img in shown], width=110)
        if not files:
            st.caption("Current images (upload new ones to replace them)")
            if st.button("Remove images", key="wiz_clear"):
                w["images"] = []
                st.rerun()

    back, nxt = _nav()
    if back:
        w["images"] = chosen()
        w["step"] = "details"
        st.rerun()
    if nxt:
        w["images"] = chosen()
        w["step"] = "review"
        st.rerun()


def _screen_review(w: dict, market) -> None:
    is_gig = w["category"] == "Gig"
    _heading("Review")

    chip = f"<span class='sh-wiz-chip'>{escape(w['deliverable'])}</span>" if w["deliverable"] else ""
    pill_cls = "" if is_gig else " rental"
    rows = [
        ("Title", w["title"], False),
        ("Rate Type", w["rate_type"], False),
        ("Rate", f"\u20b1{w['rate']:.0f}", False),
        ("Description", w["description"] or "\u2014", True),
        ("Images", ", ".join(i["name"] for i in w["images"]) or "No images uploaded", True),
    ]
    fields = "".join(
        f"<div class='sh-wiz-label'>{label}</div>"
        f"<div class='sh-wiz-value{' multi' if multi else ''}'>{escape(value)}</div>"
        for label, value, multi in rows
    )
    st.markdown(
        f"<div class='sh-wiz-typerow'>Type of Listing: "
        f"<span class='sh-wiz-pill{pill_cls}'>{'Gigs' if is_gig else 'Rentals'}</span>{chip}</div>"
        f"{fields}",
        unsafe_allow_html=True,
    )

    back, post = _nav(next_label="Post", next_key="wiz_post")
    if back:
        w["step"] = "media"
        st.rerun()
    if post:
        user = st.session_state.get("user") or {}
        result = get_listing_controller().create(
            owner_email=user.get("email", ""),
            title=w["title"],
            category=w["category"],
            rate_type=w["rate_type"],
            rate=w["rate"],
            description=w["description"],
            deliverable=w["deliverable"] or "",
            images=[(i["bytes"], i["mime"]) for i in w["images"]],
        )
        if not result.ok:
            st.error(result.error)
        else:
            _exit()
            st.session_state.selected_listing_id = result.listing.id   # open the new listing
            st.toast("Your listing has been posted!")
            st.rerun()


SCREENS = {
    "type": _screen_type,
    "deliverable": _screen_deliverable,
    "details": _screen_details,
    "media": _screen_media,
    "review": _screen_review,
}

# ==========================================
# PAGE
# ==========================================

def render_create_listing(market) -> None:
    """Draw the whole 'Create a Listing' page."""
    if "wiz" not in st.session_state:
        reset_wizard()
    w = st.session_state.wiz

    st.markdown(f"<style>{WIZARD_CSS}</style>", unsafe_allow_html=True)

    # Return to the Marketplace from any step (key "back_btn" reuses the pill
    # style of the Back button on the listing detail page)
    st.button("Back to Marketplace", key="back_btn", on_click=_exit)

    st.markdown(
        "<div class='sh-wiz-title'>Create a Listing</div>"
        "<div class='sh-wiz-sub'>Share your skills or items with the community!</div>",
        unsafe_allow_html=True,
    )

    left, right = st.columns([1, 2.3], gap="large")
    with left:
        st.markdown(_progress_html(STEP_NUMBER[w["step"]]), unsafe_allow_html=True)
    with right:
        with st.container(key="wiz_card"):
            SCREENS[w["step"]](w, market)