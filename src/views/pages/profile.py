"""Profile page (own profile): layout and dialogs only.
Rules live in ProfileController / ListingController / AuthController."""
import html

import streamlit as st

from models.listing import MAX_IMAGES, RATE_TYPES
from models.profile import Profile
from views.components.profile_components import (
    chip_html, empty_html, rating_html, render_reviews, thumb_html,
)
from views.components.styles import load_css
from views.components.session_lifecycle import sign_out_everywhere
from views.session import (
    get_auth_controller,
    get_listing_controller,
    get_profile_controller,
    refresh_session_user,
)

# NOTE: do NOT call st.set_page_config here. App.py already does it.


# ------------------------------------------------------------ state helpers
def _init():
    st.session_state.setdefault("editing", set())   # which inline editors are open
    st.session_state.setdefault("pw_round", 0)


def _email() -> str:
    return st.session_state.user["email"]


def _user():
    return get_profile_controller().get_user(_email())


def _e(value) -> str:
    return html.escape(value or "")


def _sync_session_user():
    user = _user()
    if user:
        refresh_session_user(user)


def _start_edit(name: str):
    st.session_state.editing.add(name)


def _save_field(field: str, input_key: str, edit_name: str):
    """on_change: Enter (or leaving the box) saves the value and closes the editor."""
    ctrl = get_profile_controller()
    save = {"name": ctrl.update_name, "major": ctrl.update_major}[field]
    save(_email(), st.session_state[input_key])
    _sync_session_user()
    st.session_state.editing.discard(edit_name)


def _save_about():
    get_profile_controller().update_bio(_email(), st.session_state["in_about"])
    st.session_state.editing.discard("about")


def _save_portfolio():
    get_profile_controller().update_links(
        _email(),
        st.session_state["in_portfolio"],
        st.session_state["in_linkedin"],
        st.session_state["in_github"],
    )
    st.session_state.editing.discard("portfolio")


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
    get_profile_controller().add_entries(
        st.session_state[draft_key], st.session_state.get(input_key, "")
    )
    st.session_state[input_key] = ""


def _list_editor(field_name: str, label: str, prefix: str):
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
            get_profile_controller().save_list(_email(), field_name, draft)
            st.rerun()


@st.dialog("Edit skills", width="large")
def skills_dialog():
    _list_editor("skills", "Add skills", "skills")


@st.dialog("Edit social media links", width="large")
def socials_dialog():
    _list_editor("socials", "Add social media link", "socials")


@st.dialog("Change profile photo")
def photo_dialog():
    ctrl = get_profile_controller()
    file = st.file_uploader("Choose an image", type=["png", "jpg", "jpeg"], key="photo_upload")
    if file is not None:
        error = ctrl.photo_error(file.size)
        if error:
            st.error(error)
            file = None
    if file is not None:
        st.image(file, width=160)
    with st.container(horizontal=True, horizontal_alignment="distribute"):
        if st.button("Cancel", key="photo_cancel"):
            st.rerun()
        if st.button("Save photo", key="photo_save", disabled=file is None):
            ctrl.update_photo(_email(), file.getvalue(), file.type)
            st.rerun()


@st.dialog("Change password?")
def confirm_password_dialog(current: str, new: str, verify: str):
    st.write("You’ll use your new password the next time you sign in.")
    with st.container(horizontal=True, horizontal_alignment="distribute"):
        if st.button("Cancel", key="pw_no"):
            st.rerun()
        if st.button("Yes, change it", key="pw_yes"):
            result = get_auth_controller().change_password(_email(), current, new, verify)
            if result.ok:
                st.session_state.pw_round += 1  # resets the three fields
                st.session_state.toast = "Password updated"
                st.rerun()
            else:
                st.error(result.error)


@st.dialog("Delete your account?")
def confirm_delete_dialog():
    auth = get_auth_controller()
    st.write(
        "This permanently deletes your profile, listings, gigs and rentals "
        "(including past and pending ones), and reviews. This can’t be undone."
    )
    typed = st.text_input(f"Type {auth.DELETE_CONFIRMATION} to confirm", key="del_confirm_text")
    with st.container(horizontal=True, horizontal_alignment="distribute"):
        if st.button("Cancel", key="del_no"):
            st.rerun()
        if st.button(
            "Delete account", key="del_yes",
            disabled=typed.strip() != auth.DELETE_CONFIRMATION,
        ):
            result = auth.delete_account(_email(), typed)
            if result.ok:
                sign_out_everywhere()   # back to the login page
                st.rerun()
            else:
                st.error(result.error)


# ------------------------------------------------------------ summary tab
def _inline_text(field: str, edit_name: str, display_cls: str):
    """Text that turns into a text box when its pencil is clicked.
    field is 'name' (the user's display name) or 'major' (on the profile)."""
    user = _user()
    current = user.name if field == "name" else getattr(user.profile, field)
    with st.container(horizontal=True, vertical_alignment="center", key=f"row_{edit_name}"):
        if edit_name in st.session_state.editing:
            key = f"in_{edit_name}"
            st.text_input(
                field, value=current, key=key, label_visibility="collapsed",
                on_change=_save_field, args=(field, key, edit_name),
            )
        else:
            st.markdown(f'<div class="{display_cls}">{_e(current)}</div>', unsafe_allow_html=True)
            _pencil(edit_name)


def _rating_html() -> str:
    return rating_html(get_profile_controller().get_rating_summary(_email()))


def _banner(profile: Profile):
    if profile.photo_url:
        style = f"background-image:url({html.escape(profile.photo_url, quote=True)})"
    else:
        style = ""

    with st.container(key="banner"):
        with st.container(horizontal=True, vertical_alignment="center", key="banner_row"):
            with st.container(key="avatar"):
                st.markdown(f'<div class="pf-avatar" style="{style}"></div>', unsafe_allow_html=True)
                if st.button("", key="cam_btn", icon=":material/photo_camera:"):
                    photo_dialog()
            with st.container(key="banner_info"):
                _inline_text("name", "username", "pf-name")
                _inline_text("major", "major", "pf-major")
                st.markdown(_rating_html(), unsafe_allow_html=True)


def _about(profile: Profile):
    _heading("About me", "about")
    with st.container(key="card_about"):
        if "about" in st.session_state.editing:
            st.text_area(
                "Short bio", value=profile.bio, key="in_about", height=200,
                max_chars=Profile.MAX_BIO_EDIT_LENGTH,
                label_visibility="collapsed", help="Press Ctrl+Enter to save",
            )
            with st.container(horizontal=True, horizontal_alignment="right"):
                st.button("Save", key="save_about", on_click=_save_about)
        else:
            st.markdown(f'<div class="pf-about">{_e(profile.bio)}</div>', unsafe_allow_html=True)


def _skills(profile: Profile):
    with st.container(horizontal=True, vertical_alignment="center", key="hd_skills"):
        st.markdown('<div class="pf-h2">Skills</div>', unsafe_allow_html=True)
        if st.button("", key="edit_skills", icon=":material/edit:"):
            st.session_state.draft_skills = list(profile.skills)
            skills_dialog()
    with st.container(key="card_skills"):
        st.markdown(chip_html(profile.skills), unsafe_allow_html=True)


def _portfolio(profile: Profile):
    _heading("Portfolio & Links", "portfolio")
    with st.container(key="card_portfolio"):
        if "portfolio" in st.session_state.editing:
            st.text_input("Personal Portfolio", value=profile.portfolio, key="in_portfolio")
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("LinkedIn", value=profile.linkedin, key="in_linkedin")
            with c2:
                st.text_input("Github", value=profile.github, key="in_github")
            with st.container(horizontal=True, horizontal_alignment="right"):
                st.button("Save", key="save_portfolio", on_click=_save_portfolio)
        else:
            st.markdown('<div class="pf-label">Personal Portfolio</div>'
                        f'<div class="pf-pill">{_e(profile.portfolio) or "&nbsp;"}</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            c1.markdown('<div class="pf-label" style="margin-top:1rem">LinkedIn</div>'
                        f'<div class="pf-pill">{_e(profile.linkedin) or "&nbsp;"}</div>', unsafe_allow_html=True)
            c2.markdown('<div class="pf-label" style="margin-top:1rem">Github</div>'
                        f'<div class="pf-pill">{_e(profile.github) or "&nbsp;"}</div>', unsafe_allow_html=True)


def _socials(profile: Profile):
    with st.container(horizontal=True, vertical_alignment="center", key="hd_socials"):
        st.markdown('<div class="pf-h2">Social Media Contacts</div>', unsafe_allow_html=True)
        if st.button("", key="edit_socials", icon=":material/edit:"):
            st.session_state.draft_socials = list(profile.socials)
            socials_dialog()
    with st.container(key="card_socials"):
        st.markdown(chip_html(profile.socials, wide=True), unsafe_allow_html=True)


# ------------------------------------------------------------ my listings
def _open_edit_listing(listing):
    """Start an edit session: the draft holds the images while the dialog is open."""
    st.session_state.edit_listing_draft = {"id": listing.id, "images": list(listing.images)}
    edit_listing_dialog(listing.id)


def _close_edit_listing():
    st.session_state.pop("edit_listing_draft", None)
    st.rerun()


@st.dialog("Edit Listing", width="large")
def edit_listing_dialog(lid: int):
    lc = get_listing_controller()
    l = lc.get(_email(), lid)
    draft = st.session_state.get("edit_listing_draft")
    if l is None or not draft or draft["id"] != lid:
        st.error("This listing is no longer available.")
        return
    images: list = draft["images"]

    with st.container(key="listing_form"):
        is_gig = l.category == "Gig"
        chip = f'<span class="lf-chip">{_e(l.deliverable)}</span>' if l.deliverable else ""
        st.markdown(
            f'<div class="lf-typerow">Type of Listing: '
            f'<span class="lf-pill{"" if is_gig else " rental"}">{"Gigs" if is_gig else "Rentals"}</span>{chip}</div>',
            unsafe_allow_html=True,
        )

        title = st.text_input("Title", value=l.title, key=f"lf_title_{lid}")
        rate_type = st.selectbox(
            "Rate Type", RATE_TYPES, index=RATE_TYPES.index(l.rate_type), key=f"lf_rate_type_{lid}"
        )
        rate = st.number_input(
            "Rate (₱)", min_value=0.0, step=50.0, value=float(l.price), key=f"lf_rate_{lid}"
        )
        description = st.text_area("Description", value=l.description, height=110, key=f"lf_desc_{lid}")

        # ---- images: current ones (removable) + new uploads ----
        st.markdown('<div class="lf-label">Images</div>', unsafe_allow_html=True)
        if images:
            with st.container(horizontal=True, key="lf_thumbs"):
                for i, uri in enumerate(images):
                    with st.container(key=f"lf_thumb_{i}"):
                        st.markdown(
                            f'<div class="lf-thumb" style="background-image:url({uri})"></div>',
                            unsafe_allow_html=True,
                        )
                        if st.button("✕", key=f"lf_rm_{i}"):
                            images.pop(i)
                            st.rerun(scope="fragment")  # keep the dialog open

        room = MAX_IMAGES - len(images)
        files = st.file_uploader(
            "Add images", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True,
            key=f"lf_files_{lid}", label_visibility="collapsed", disabled=room <= 0,
        )
        if len(files) > room:
            st.warning(f"You can have up to {MAX_IMAGES} images, so only the first {max(room, 0)} new ones will be added.")
            files = files[: max(room, 0)]
        if files:
            st.image([f.getvalue() for f in files], width=110)
            st.caption("New images are added when you save")
        st.markdown(
            f'<div class="lf-count">{len(images) + len(files)} of {MAX_IMAGES} images</div>',
            unsafe_allow_html=True,
        )

        error_slot = st.container()
        with st.container(horizontal=True, horizontal_alignment="distribute"):
            if st.button("Cancel", key="lf_cancel"):
                _close_edit_listing()
            if st.button("Save changes", key="lf_save"):
                error = lc.update(
                    _email(), lid, title, rate_type, rate, description,
                    kept_images=images,
                    new_images=[(f.getvalue(), f.type or "image/png") for f in files],
                )
                if error:
                    error_slot.error(error)
                else:
                    _close_edit_listing()


@st.dialog("Close this listing?")
def close_listing_dialog(lid: int):
    lc = get_listing_controller()
    l = lc.get(_email(), lid)
    st.write(f"“{l.title}” will no longer be visible to other students. You can reopen it later.")
    with st.container(horizontal=True, horizontal_alignment="distribute"):
        if st.button("Cancel", key="lst_close_no"):
            st.rerun()
        if st.button("Yes, close it", key="lst_close_yes"):
            lc.close(_email(), lid)
            st.rerun()


@st.dialog("Delete this listing?")
def delete_listing_dialog(lid: int):
    lc = get_listing_controller()
    l = lc.get(_email(), lid)
    st.write(f"“{l.title}” will be permanently deleted. This can’t be undone.")
    with st.container(horizontal=True, horizontal_alignment="distribute"):
        if st.button("Cancel", key="lst_del_no"):
            st.rerun()
        if st.button("Delete listing", key="lst_del_yes"):
            lc.delete(_email(), lid)
            st.rerun()


def _toggle_menu(lid: int):
    """Three-dots button: open this card's menu (closing any other), or close it."""
    current = st.session_state.get("open_listing_menu")
    st.session_state.open_listing_menu = None if current == lid else lid


def _menu_action(action: str, lid: int):
    """Menu item clicked: close the menu and queue the action for this run."""
    st.session_state.open_listing_menu = None
    if action == "reopen":
        get_listing_controller().reopen(_email(), lid)
    else:
        st.session_state.listing_action = (action, lid)


def _run_listing_action():
    """Open the dialog queued by the menu (once), outside any card."""
    action = st.session_state.pop("listing_action", None)
    if not action:
        return
    kind, lid = action
    listing = get_listing_controller().get(_email(), lid)
    if listing is None:
        return
    if kind == "edit":
        _open_edit_listing(listing)
    elif kind == "close":
        close_listing_dialog(lid)
    elif kind == "delete":
        delete_listing_dialog(lid)


def _listing_card(l):
    lid = l.id
    with st.container(key=f"lcard_{lid}"):
        badge = "Closed" if l.is_closed else l.price_label
        st.markdown(thumb_html(l, badge, closed=l.is_closed), unsafe_allow_html=True)
        st.markdown(f'<div class="pf-listing-name">{html.escape(l.title)}</div>', unsafe_allow_html=True)

        # Rendered last; CSS floats both over the image (three dots, then the open menu).
        with st.container(key=f"menu_{lid}"):
            st.button("Options", key=f"menu_btn_{lid}", on_click=_toggle_menu, args=(lid,))
        if st.session_state.get("open_listing_menu") == lid:
            with st.container(key=f"lpanel_{lid}"):
                st.button("Edit listing", key=f"mi_edit_{lid}", icon=":material/edit:",
                          width="stretch", on_click=_menu_action, args=("edit", lid))
                if l.is_closed:
                    st.button("Reopen listing", key=f"mi_open_{lid}", icon=":material/lock_open:",
                              width="stretch", on_click=_menu_action, args=("reopen", lid))
                else:
                    st.button("Close listing", key=f"mi_close_{lid}", icon=":material/block:",
                              width="stretch", on_click=_menu_action, args=("close", lid))
                st.button("Delete listing", key=f"mi_del_{lid}", icon=":material/delete:",
                          width="stretch", on_click=_menu_action, args=("delete", lid))


def _listings():
    listings = get_listing_controller().get_for_owner(_email())
    reviews = get_profile_controller().get_reviews(_email())
    t1, t2 = st.tabs(["My Listings", "Reviews"])
    with t1:
        if not listings:
            st.markdown(empty_html("You have no listings yet."), unsafe_allow_html=True)
        else:
            with st.container(horizontal=True, key="listing_row"):
                for l in listings:
                    _listing_card(l)
    with t2:
        render_reviews(reviews)


def _summary_tab(profile: Profile):
    # Row 1: profile banner across the full width
    _banner(profile)

    # Row 2: About me across the full width
    _about(profile)

    # Row 3: Portfolio & Links on the left, Social Media and Skills stacked on the right
    portfolio_col, right_col = st.columns([1.5, 2.5])
    with portfolio_col:
        _portfolio(profile)
    with right_col:
        _socials(profile)
        _skills(profile)

    _listings()
    _run_listing_action()


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
            with st.container(horizontal=True, horizontal_alignment="center"):
                clicked = st.button("Confirm", key="pw_confirm")
            if clicked:
                error = get_auth_controller().validate_password_change(_email(), cur, new, ver)
                if error:
                    st.error(error)
                else:
                    confirm_password_dialog(cur, new, ver)

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
    user = _user()
    if user is None:            # stale session (e.g. server restarted): log in again
        sign_out_everywhere()
        st.rerun()

    load_css("profile", "listing_form")

    if "toast" in st.session_state:
        st.toast(st.session_state.pop("toast"))

    st.title("Profile Information")
    st.caption("Keep your profile up to date to build trust with other students")

    summary, settings = st.tabs(["Summary", "Settings"])
    with summary:
        _summary_tab(user.profile)
    with settings:
        _settings_tab()


render_profile()