"""Read-only profile page for OTHER users (no edit buttons, no settings).

Same layout as the "Profile Information" page: banner -> About me ->
Portfolio & Links | Social Media + Skills -> Listings / Reviews tabs.

Usage:
    from user_profile_view import render_user_profile
    render_user_profile("Ana R.", on_back=my_back_callback)

Keep this file NEXT TO app.py (not inside pages/), or Streamlit will list it as a page.
"""
import base64
import html

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Montserrat:wght@700;800&display=swap');

:root {
    --teal: #0f6b62;
    --teal-hover: #0b5750;
    --mint: #4ccfc0;
    --ink: #3a3d3f;
    --muted: #5b6770;
    --field: #e8edf1;
}

/* ---------- main area ---------- */
[data-testid="stMain"] { background: #ffffff; color: var(--ink); }
[data-testid="stMain"] p,
[data-testid="stMain"] button { font-family: 'Inter', sans-serif; }
[data-testid="stMain"] h1 { font-family: 'Montserrat', sans-serif; font-weight: 800; color: var(--ink); padding-bottom: 0; }
[data-testid="stMain"] h2, [data-testid="stMain"] h3 { color: var(--ink); }

[data-testid="stMainBlockContainer"] { padding-top: 1.5rem !important; padding-bottom: 3rem !important; }
[data-testid="stMainBlockContainer"], .block-container {
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    max-width: 100% !important;
}

.pf-h2 { font-family: 'Montserrat', sans-serif; font-weight: 700; font-size: 1.5rem; color: var(--ink); line-height: 1.2; margin: 0; padding-bottom: 0.75rem; }

/* ---------- back button (top left) ---------- */
.st-key-up_back button {
    background: #ffffff !important;
    border: 1.5px solid var(--teal) !important;
    border-radius: 999px !important;
    min-height: 1.9rem;
    padding: 0 1.1rem !important;
    box-shadow: none;
}
.st-key-up_back button p { color: var(--teal) !important; font-weight: 600; font-size: 0.85rem; }
.st-key-up_back button:hover { background: #effaf8 !important; }

/* ---------- tabs ---------- */
[data-testid="stMain"] [data-testid="stTab"] {
    background: transparent;
    min-width: 11rem;
    justify-content: center;
    padding: 0.6rem 1rem;
}
[data-testid="stMain"] [data-testid="stTab"] [data-testid="stMarkdownContainer"] p {
    font-family: 'Montserrat', sans-serif;
    font-size: 1rem;
    color: #3a3d3f !important;
    font-weight: 600;
}
[data-testid="stMain"] [data-testid="stTab"]:hover [data-testid="stMarkdownContainer"] p { color: #0f6b62 !important; }
[data-testid="stMain"] [data-testid="stTab"][aria-selected="true"] [data-testid="stMarkdownContainer"] p {
    color: #0f6b62 !important;
    font-weight: 700;
}
[data-testid="stMain"] [data-testid="stTab"] .react-aria-SelectionIndicator,
[data-testid="stMain"] [data-baseweb="tab-highlight"] { background-color: #0f6b62 !important; }

/* ---------- banner ---------- */
.st-key-banner { background: var(--field); border-radius: 18px; padding: 1.3rem 2rem 1.8rem 2rem; margin-top: 0.5rem; }
.st-key-avatar { width: 128px !important; min-width: 128px !important; max-width: 128px !important; height: 128px; flex: 0 0 128px !important; margin-right: 0 !important; }
.pf-avatar {
    width: 128px; height: 128px; border-radius: 50%; border: 3px solid var(--mint);
    background: #f3f6f8 center/cover no-repeat; box-sizing: border-box;
    display: flex; align-items: center; justify-content: center;
    font-family: 'Montserrat', sans-serif; font-weight: 800; font-size: 3rem; color: var(--teal);
}
.pf-name { font-family: 'Montserrat', sans-serif; font-weight: 800; font-size: 1.9rem; line-height: 1.2; color: var(--ink); }
.pf-major { font-size: 1rem; color: var(--ink); }
.pf-rating { font-size: 0.9rem; color: var(--muted); margin-top: 0.3rem; }
.pf-rating .star { color: #fbc02d; margin-right: 0.4rem; }
.st-key-banner_row > [data-testid="stLayoutWrapper"]:has(.st-key-avatar) { flex: 0 0 128px !important; width: 128px !important; min-width: 128px !important; }
.st-key-banner_row > [data-testid="stLayoutWrapper"]:has(.st-key-banner_info) { flex: 1 1 0 !important; width: auto !important; min-width: 0; }
.st-key-banner_row { gap: 3rem !important; }

/* ---------- section cards ---------- */
[class*="st-key-card_"] { background: #ffffff; border-radius: 18px; padding: 1rem 1.2rem 1.3rem 1.2rem !important; box-shadow: 0 2px 12px rgba(27, 42, 65, 0.14); gap: 0.5rem; }
.st-key-card_skills, .st-key-card_socials { padding-bottom: 0.5rem !important; }
.st-key-card_about { padding-bottom: 2rem !important; }
.st-key-card_portfolio { padding-bottom: 1.9rem !important; padding-top: 0.6rem !important; }
.pf-about { font-size: 0.9rem; line-height: 1.5; color: var(--ink); white-space: pre-wrap; }
.pf-empty { font-size: 0.9rem; color: #8a949c; }
.pf-chip { display: inline-block; background: var(--field); border-radius: 999px; padding: 0.3rem 0.9rem; margin: 0 0.5rem 0.5rem 0; font-weight: 500; font-size: 0.8rem; color: var(--ink); }
.pf-chip.wide { padding: 0.4rem 1.3rem; }
.pf-label { font-weight: 600; font-size: 1rem; color: var(--ink); margin: 0 0 0.3rem 0.3rem; }
.pf-pill { background: var(--field); border-radius: 999px; padding: 0.6rem 1.1rem; text-align: center; font-size: 1.05rem; word-break: break-all; min-height: 2.6rem; }
.pf-pill a { color: var(--teal) !important; text-decoration: none; font-weight: 600; }
.pf-pill a:hover { text-decoration: underline; }

/* ---------- listings: horizontal scroller ---------- */
.pf-thumb { position: relative; height: 150px; border-radius: 14px; overflow: hidden;
    background:
      radial-gradient(ellipse 55% 38% at 22% 108%, #c5dc7a 0 98%, transparent 100%),
      radial-gradient(ellipse 75% 45% at 72% 112%, #8aa300 0 98%, transparent 100%),
      linear-gradient(#bee3fa, #e8f5fd); }
.pf-price { position: absolute; top: 10px; right: 10px; background: #fff; border-radius: 999px; padding: 2px 12px; font-size: 0.75rem; font-weight: 600; color: var(--ink); }
.pf-listing-name { font-family: 'Montserrat', sans-serif; font-weight: 700; font-size: 1rem; line-height: 1.3; color: var(--ink); margin-top: 1rem; }
.pf-review { background: #fff; border-radius: 18px; padding: 1rem 1.2rem; box-shadow: 0 2px 12px rgba(27, 42, 65, 0.14); margin-bottom: 0.8rem; font-size: 0.9rem; line-height: 1.5; color: var(--ink); }

.st-key-listing_row { flex-wrap: nowrap !important; overflow-x: auto; gap: 1rem !important; padding: 0.5rem 0.5rem 1.2rem 0.5rem; }
.st-key-listing_row > * { flex: 0 0 340px !important; width: 340px !important; min-width: 340px !important; }
[class*="st-key-lcard_"] { background: #fff; border-radius: 18px; padding: 0.8rem 0.8rem 1.3rem 0.8rem !important; box-shadow: 0 2px 12px rgba(27, 42, 65, 0.14); gap: 1.3rem; }
[class*="st-key-lcard_"] .pf-thumb { height: 190px; display: block; flex-shrink: 0; }
[class*="st-key-lcard_"] .pf-listing-name { margin: 0; padding: 0.2rem 0.5rem 0.4rem 0.5rem; font-size: 1.1rem; line-height: 1.35; min-height: 3.2rem; white-space: normal; overflow-wrap: anywhere; word-break: break-word; }
</style>
"""


# ------------------------------------------------------------ sample data
# TODO: replace get_user() with a database lookup.
# (name, major, skills, rating, review count, [(listing, price per day)])
_SEED = [
    ("Ana R.", "Bachelor of Mathematics", ["Calculus", "Statistics", "Tutoring"], 4.9, 87,
     [("Math Tutoring (Calculus)", 500), ("Essay Editing", 200)]),
    ("Miguel S.", "Bachelor of Fine Arts", ["Photography", "Lightroom", "Videography"], 4.8, 54,
     [("Event Photography", 1200)]),
    ("Carla D.", "Bachelor of Design", ["Figma", "Illustrator", "Branding"], 4.7, 41,
     [("Poster Design", 400)]),
    ("Dan K.", "Bachelor of English", ["Proofreading", "Academic Writing"], 4.6, 29,
     [("Thesis Proofreading", 300)]),
    ("Nina T.", "Bachelor of Veterinary Science", ["Pet Care", "Dog Training"], 4.9, 63,
     [("Dog Walking", 250)]),
    ("Josh P.", "Bachelor of Music", ["Guitar", "Music Theory"], 4.8, 35,
     [("Guitar Lessons", 350)]),
    ("Sam W.", "Bachelor of Business", ["Resumes", "Career Coaching"], 4.5, 22,
     [("Resume Review", 400)]),
    ("Leo M.", "Bachelor of Computer Science", ["Python", "Data Structures", "Tutoring"], 4.7, 48,
     [("Python Tutoring", 450)]),
    ("Rico B.", "Bachelor of Media Arts", ["Video Editing", "Premiere Pro"], 4.8, 39,
     [("Video Editing", 800)]),
    ("Mia L.", "Bachelor of Graphic Design", ["Logo Design", "Illustrator"], 4.9, 71,
     [("Logo Design", 600)]),
    ("Paolo G.", "Bachelor of Film", ["Videography", "Color Grading"], 4.6, 18,
     [("Wedding Videography", 1500)]),
    ("Kyla V.", "Bachelor of Marketing", ["Social Media", "Copywriting"], 4.7, 33,
     [("Social Media Management", 350)]),
]

_REVIEWS = [
    ("Student A", 5.0, "Clear communication and always on time."),
    ("Student B", 5.0, "Great work, would happily hire again."),
]


def _build_user(name, major, skills, rating, n_reviews, listings) -> dict:
    handle = name.split()[0].lower()
    return {
        "username": name,
        "major": major,
        "bio": f"Hi, I'm {name}! I'm a student who enjoys helping others with "
               f"{', '.join(skills[:2]).lower() if skills else 'all kinds of gigs'}. "
               "Message me anytime if you'd like to work together.",
        "skills": skills,
        "portfolio": "",
        "linkedin": "",
        "github": "",
        "socials": [f"{handle}@hive.com"],
        "photo": None,   # (bytes, mime) or None
        "rating": rating,
        "review_count": n_reviews,
        "listings": [{"id": i, "name": n, "price": p, "status": "open"}
                     for i, (n, p) in enumerate(listings)],
        "reviews": _REVIEWS,
    }


USERS = {row[0]: _build_user(*row) for row in _SEED}


def get_user(name: str) -> dict:
    """Look a user up by display name. Unknown names get an empty-ish profile."""
    return USERS.get(name) or _build_user(name, "Student", [], 0.0, 0, [])


# ------------------------------------------------------------ pieces
def _link_html(value: str) -> str:
    if not value:
        return "&nbsp;"
    safe = html.escape(value)
    if value.startswith(("http://", "https://")):
        return f'<a href="{safe}" target="_blank" rel="noopener noreferrer">{safe}</a>'
    return safe


def _chip_html(items, wide=False) -> str:
    if not items:
        return '<div class="pf-empty">Nothing added yet.</div>'
    cls = "pf-chip wide" if wide else "pf-chip"
    return "".join(f'<span class="{cls}">{html.escape(i)}</span>' for i in items)


def _heading(text: str) -> None:
    st.markdown(f'<div class="pf-h2">{html.escape(text)}</div>', unsafe_allow_html=True)


def _banner(u: dict) -> None:
    if u["photo"]:
        data, mime = u["photo"]
        style = f"background-image:url(data:{mime};base64,{base64.b64encode(data).decode()})"
        initial = ""
    else:
        style = ""
        initial = html.escape(u["username"][:1].upper())

    if u["review_count"]:
        rating = f'<span class="star">★</span>{u["rating"]:.1f} ({u["review_count"]} reviews)'
    else:
        rating = "No reviews yet"

    with st.container(key="banner"):
        with st.container(horizontal=True, vertical_alignment="center", key="banner_row"):
            with st.container(key="avatar"):
                st.markdown(f'<div class="pf-avatar" style="{style}">{initial}</div>', unsafe_allow_html=True)
            with st.container(key="banner_info"):
                st.markdown(f'<div class="pf-name">{html.escape(u["username"])}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="pf-major">{html.escape(u["major"])}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="pf-rating">{rating}</div>', unsafe_allow_html=True)


def _about(u: dict) -> None:
    _heading("About me")
    with st.container(key="card_about"):
        if u["bio"]:
            st.markdown(f'<div class="pf-about">{html.escape(u["bio"])}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="pf-empty">No bio yet.</div>', unsafe_allow_html=True)


def _portfolio(u: dict) -> None:
    _heading("Portfolio & Links")
    with st.container(key="card_portfolio"):
        st.markdown('<div class="pf-label">Personal Portfolio</div>'
                    f'<div class="pf-pill">{_link_html(u["portfolio"])}</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.markdown('<div class="pf-label" style="margin-top:1rem">LinkedIn</div>'
                    f'<div class="pf-pill">{_link_html(u["linkedin"])}</div>', unsafe_allow_html=True)
        c2.markdown('<div class="pf-label" style="margin-top:1rem">Github</div>'
                    f'<div class="pf-pill">{_link_html(u["github"])}</div>', unsafe_allow_html=True)


def _socials(u: dict) -> None:
    _heading("Social Media Contacts")
    with st.container(key="card_socials"):
        st.markdown(_chip_html(u["socials"], wide=True), unsafe_allow_html=True)


def _skills(u: dict) -> None:
    _heading("Skills")
    with st.container(key="card_skills"):
        st.markdown(_chip_html(u["skills"]), unsafe_allow_html=True)


def _listing_card(l: dict) -> None:
    with st.container(key=f"lcard_{l['id']}"):
        st.markdown(f'<div class="pf-thumb"><span class="pf-price">₱{l["price"]:,}/day</span></div>',
                    unsafe_allow_html=True)
        st.markdown(f'<div class="pf-listing-name">{html.escape(l["name"])}</div>', unsafe_allow_html=True)


def _listings(u: dict) -> None:
    t1, t2 = st.tabs(["Listings", "Reviews"])
    with t1:
        open_listings = [l for l in u["listings"] if l["status"] == "open"]
        if not open_listings:
            st.markdown('<div class="pf-empty">No listings yet.</div>', unsafe_allow_html=True)
        else:
            with st.container(horizontal=True, key="listing_row"):
                for l in open_listings:
                    _listing_card(l)
    with t2:
        if not u["reviews"] or not u["review_count"]:
            st.markdown('<div class="pf-empty">No reviews yet.</div>', unsafe_allow_html=True)
        for who, stars, text in (u["reviews"] if u["review_count"] else []):
            st.markdown(
                f'<div class="pf-review"><b>{html.escape(who)}</b> · ★ {stars:.1f}<br>{html.escape(text)}</div>',
                unsafe_allow_html=True,
            )


# ------------------------------------------------------------ entry
def render_user_profile(name: str, on_back) -> None:
    """Draw another user's profile. `on_back` is called (as a button callback) when Back is pressed."""
    u = get_user(name)
    st.markdown(CSS, unsafe_allow_html=True)

    st.button("← Back", key="up_back", on_click=on_back)
    _banner(u)
    _about(u)

    portfolio_col, right_col = st.columns([1.5, 2.5])
    with portfolio_col:
        _portfolio(u)
    with right_col:
        _socials(u)
        _skills(u)

    _listings(u)