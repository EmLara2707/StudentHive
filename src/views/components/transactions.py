"""Gigs and Rentals pages: one template, parameterised by TransactionKind.

Layout only. Which transactions belong to which tab, the calendar expansion, the
to-do ordering and every status change live in TransactionController; the wording
that differs between Gigs and Rentals lives in _COPY below.

Each page file calls render_transactions(kind). Styles: views/styles/transactions.css.
"""
from dataclasses import dataclass
from datetime import date
from html import escape

import calendar

import streamlit as st

from controllers.transaction_controller import NOT_FOUND_ERROR, TransactionController
from models.transaction import (
    Action, Role, TodoStep, TodoTask, TransactionEntry, TransactionKind,
    TransactionStatus,
)
from repositories.errors import RepositoryError
from utils.clock import today_manila
from utils.dates import first_of_month, shift_month
from views.components.repo_errors import loading, show_error
from views.components.styles import load_css
from views.components.user_profile import open_profile, render_open_profile
from views.session import get_current_email, get_transaction_controller

# NOTE: do NOT call st.set_page_config here. App.py already does it.

# ---------- Layout sizes (px) ----------
# Tune these to fit your screen. The page itself never scrolls;
# only the boxes below scroll internally if their content is taller.
LIST_H = 680     # left box: lists
CAL_H = 680      # left box: calendar (taller than the lists)
TODO_H = 680     # right box: to-do list / details
DIVIDER_H = 780  # vertical bar between the left and right sides

PENDING_FILTERS = {"Requests to me": True, "Requests I sent": False}   # label -> incoming?
CANCELLED_FILTERS = {"Cancelled by me": True, "Cancelled by others": False}   # label -> by me?


# ------------------------------------------------------------ wording
@dataclass(frozen=True)
class _Copy:
    """Everything on the page that reads differently for Gigs and Rentals."""
    scope: str            # open_profile scope, so each page shows its own profile view
    prefix: str           # namespaces session keys: Gigs and Rentals never share state
    noun: str
    title: str
    caption: str
    mine_tab: str
    details_title: str
    empty_mine: str
    empty_done: str
    empty_cancel: str
    mine_filters: dict    # label -> Role
    done_filters: dict
    legend: tuple         # ((Role, text), ...) in display order
    who_label: dict       # Role -> "For" / "By" ... on the cards
    user_label: dict      # Role -> label of the other person's row in the details panel
    review_who: dict      # Role -> "client" / "provider" ... in the review placeholder
    todo: dict            # (Role, TodoStep) -> (title, subtitle) templates
    note_waiting: str     # I asked and am waiting
    note_respond: str     # they asked and I must answer
    note_completed: str
    reject_text: str
    accept_text: str
    withdraw_text: str
    complete_title: str
    cancel_title: str
    keep_label: str


_COPY = {
    TransactionKind.GIG: _Copy(
        scope="gigs", prefix="gig", noun="gig", title="Gigs",
        caption="Manage and track your gigs and review past transactions.",
        mine_tab="My Gigs", details_title="Gig Details",
        empty_mine="No gigs to show.", empty_done="No completed gigs.",
        empty_cancel="No cancelled gigs.",
        mine_filters={"Hiring": Role.HIRING, "Doing": Role.DOING},
        done_filters={"Gigs I provided": Role.DOING, "Gigs I booked": Role.HIRING},
        legend=((Role.HIRING, "Hiring (gigs you booked)"), (Role.DOING, "Doing (gigs you offered)")),
        who_label={Role.DOING: "For", Role.HIRING: "By"},
        user_label={Role.DOING: "Client (the person who booked you)",
                    Role.HIRING: "Provider (the person you booked)"},
        review_who={Role.DOING: "client", Role.HIRING: "provider"},
        todo={
            (Role.DOING, TodoStep.RESPOND): ("Respond to request: {item}", "{name} wants to hire you"),
            (Role.DOING, TodoStep.BEGIN): ("Start {item}", "For {name}"),
            (Role.DOING, TodoStep.FINISH): ("Deliver {item}", "To {name}"),
            (Role.HIRING, TodoStep.BEGIN): ("{item} begins", "By {name}"),
            (Role.HIRING, TodoStep.FINISH): ("Review & pay for {item}", "To {name}"),
        },
        note_waiting="Waiting for {name} to approve your request.",
        note_respond="{name} is waiting for your response.",
        note_completed="This gig was completed.",
        reject_text="{name}'s request to hire you for “{item}” will be declined.",
        accept_text="You'll provide “{item}” for {name} from {dates}.",
        withdraw_text="Your request to hire {name} for “{item}” will be withdrawn.",
        complete_title="Complete this gig?", cancel_title="Cancel this gig?",
        keep_label="Keep gig",
    ),
    TransactionKind.RENTAL: _Copy(
        scope="rentals", prefix="rent", noun="rental", title="Rentals",
        caption="Manage and track your rentals and review past transactions.",
        mine_tab="My Rentals", details_title="Rental Details",
        empty_mine="No rentals to show.", empty_done="No completed rentals.",
        empty_cancel="No cancelled rentals.",
        mine_filters={"Renting": Role.RENTING, "Lending": Role.LENDING},
        done_filters={"Items I rented": Role.RENTING, "Items I rented out": Role.LENDING},
        legend=((Role.RENTING, "Renting (rentals you took)"),
                (Role.LENDING, "Lending (rentals you offered)")),
        who_label={Role.RENTING: "From", Role.LENDING: "To"},
        user_label={Role.RENTING: "Owner", Role.LENDING: "Renter"},
        review_who={Role.RENTING: "owner", Role.LENDING: "renter"},
        todo={
            (Role.LENDING, TodoStep.RESPOND): ("Respond to request: {item}", "{name} wants to rent it"),
            (Role.RENTING, TodoStep.BEGIN): ("Pick up {item}", "From {name}"),
            (Role.RENTING, TodoStep.FINISH): ("Return {item}", "To {name}"),
            (Role.LENDING, TodoStep.BEGIN): ("Hand over {item}", "To {name}"),
            (Role.LENDING, TodoStep.FINISH): ("Collect {item} back", "From {name}"),
        },
        note_waiting="Waiting for {name} to approve your request.",
        note_respond="{name} is waiting for your response.",
        note_completed="This rental was completed.",
        reject_text="{name}'s request to rent “{item}” will be declined.",
        accept_text="{name} will be able to rent “{item}” from {dates}.",
        withdraw_text="Your request to rent “{item}” from {name} will be withdrawn.",
        complete_title="Complete this rental?", cancel_title="Cancel this rental?",
        keep_label="Keep rental",
    ),
}

_ACTION_TITLES = {
    Action.ACCEPT: "Accept this request?",
    Action.REJECT: "Reject this request?",
    Action.WITHDRAW: "Cancel this request?",
}
# widget-key stems of each confirmation dialog (kept from the old pages)
_DIALOG_KEYS = {Action.ACCEPT: "accept", Action.REJECT: "reject", Action.COMPLETE: "complete",
                Action.CANCEL: "cancel", Action.WITHDRAW: "creq"}


@dataclass(frozen=True)
class _Ctx:
    """What every helper needs: this page's wording, the controller, who I am, today."""
    kind: TransactionKind
    copy: _Copy
    ctrl: TransactionController
    email: str
    today: date

    def key(self, name: str) -> str:
        """Session-state key private to this page (Gigs and Rentals don't share state)."""
        return f"{self.copy.prefix}_{name}"


# ------------------------------------------------------------ formatting helpers
def fmt_range(r: TransactionEntry) -> str:
    tx = r.transaction
    if tx.start == tx.end:
        return f"{tx.start:%b} {tx.start.day}"
    return f"{tx.start:%b} {tx.start.day} – {tx.end:%b} {tx.end.day}"


def plural(n: int, word: str) -> str:
    return f"{n} {word}" + ("" if n == 1 else "s")


def _money(amount: float) -> str:
    return f"₱{amount:,.0f}" if float(amount).is_integer() else f"₱{amount:,.2f}"


def _duration(r: TransactionEntry) -> str | None:
    tx = r.transaction
    if tx.unit == "day":
        return plural(int(tx.quantity), "day")
    if tx.unit == "hr":
        return f"{tx.quantity:g} " + ("hr" if tx.quantity == 1 else "hrs")
    return None


def _time_range(r: TransactionEntry) -> str | None:
    tx = r.transaction
    if not (tx.is_hourly and tx.start_time and tx.end_time):
        return None
    fmt = lambda t: f"{t.hour % 12 or 12}:{t.minute:02d} {'AM' if t.hour < 12 else 'PM'}"
    return f"{fmt(tx.start_time)} – {fmt(tx.end_time)}"


# ------------------------------------------------------------ html builders
def badges_html(r: TransactionEntry) -> str:
    out = f'<span class="badge badge-{r.role.value.lower()}">{escape(r.role.value)}</span>'
    if r.status is TransactionStatus.PENDING:
        out += '<span class="badge badge-pending">Pending</span>'
    if r.status is TransactionStatus.CANCELLED:
        who = "by you" if r.cancelled_by_me else "by them"
        out += f'<span class="badge badge-cancelled">Cancelled {who}</span>'
    return out


def card_info_html(ctx: _Ctx, r: TransactionEntry) -> str:
    """Single-line HTML (no indentation, so Markdown doesn't treat it as code)."""
    who_label = ctx.copy.who_label[r.role]
    return (
        '<div class="listing-info">'
        f'<div class="listing-name">{escape(r.transaction.item)}</div>'
        f'<div class="listing-sub">{fmt_range(r)} · {who_label} {escape(r.counterpart.name)}</div>'
        f'<div class="listing-meta">{badges_html(r)}'
        f'<span class="listing-price">{escape(r.transaction.price_label)}</span></div>'
        '</div>'
    )


def todo_row(due: date, title: str, sub: str, today: date) -> str:
    days = (due - today).days
    if days < 0:
        when, level = f"Overdue {-days}d", "overdue"
    elif days == 0:
        when, level = "Today", "soon"
    elif days == 1:
        when, level = "Tomorrow", "soon"
    else:
        when, level = f"In {days} days", ""
    row_cls = f"todo-{level}" if level else ""
    when_cls = f"todo-when-{level}" if level else ""
    return (
        f'<div class="todo-row {row_cls}">'
        '<div class="todo-info">'
        f'<div class="todo-title">{escape(title)}</div>'
        f'<div class="todo-sub">{escape(sub)} · {due:%b} {due.day}</div>'
        '</div>'
        f'<div class="todo-when {when_cls}">{when}</div>'
        '</div>'
    )


def detail_top_html(r: TransactionEntry) -> str:
    return (
        f'<img class="det-img" src="{escape(r.transaction.image)}">'
        f'<div class="det-title">{escape(r.transaction.item)}</div>'
        f'<div class="det-badges">{badges_html(r)}</div>'
    )


def detail_user_row_html(ctx: _Ctx, r: TransactionEntry) -> str:
    label = ctx.copy.user_label[r.role]
    return (
        f'<div class="det-row"><span class="det-label">{escape(label)}</span>'
        f'<span class="det-value det-link">{escape(r.counterpart.name)} ›</span></div>'
    )


def _status_note(ctx: _Ctx, r: TransactionEntry) -> tuple[str, str]:
    """The grey note under the details, and an extra CSS class for it."""
    tx, today, name = r.transaction, ctx.today, r.counterpart.name
    if r.status is TransactionStatus.CANCELLED:
        return ("Cancelled by you." if r.cancelled_by_me else f"Cancelled by {name}."), ""
    if r.status is TransactionStatus.COMPLETED:
        return ctx.copy.note_completed, ""
    if r.status is TransactionStatus.PENDING:
        text = ctx.copy.note_respond if r.is_provider else ctx.copy.note_waiting
        return text.format(name=name), ""
    if today < tx.start:
        return f"Starts in {plural((tx.start - today).days, 'day')}.", ""
    if today <= tx.end:
        left = (tx.end - today).days
        return ("In progress — ends today." if left == 0
                else f"In progress — ends in {plural(left, 'day')}."), ""
    return f"Overdue by {plural((today - tx.end).days, 'day')}.", " det-note-overdue"


def detail_bottom_html(ctx: _Ctx, r: TransactionEntry) -> str:
    tx = r.transaction
    note, note_cls = _status_note(ctx, r)

    rows: list[tuple[str, str, bool]] = []     # (label, value, long text?)
    if tx.deadline is not None:
        rows.append(("Deadline", f"{tx.deadline:%b} {tx.deadline.day}", False))
    else:
        rows.append(("Dates", fmt_range(r), False))
    if _time_range(r):
        rows.append(("Time", _time_range(r), False))
    if _duration(r):
        rows.append(("Duration", _duration(r), False))
    rows.append(("Price" if tx.unit == "once" else "Rate", tx.price_label, False))
    rows.append(("Estimated total", _money(tx.total), False))
    if tx.meeting_mode:
        rows.append(("Meeting", tx.meeting_mode, False))
    if tx.location:
        rows.append(("Location", tx.location, True))
    if tx.project_details:
        rows.append(("Project details", tx.project_details, True))

    rows_html = "".join(
        f'<div class="det-row"><span class="det-label">{escape(label)}</span>'
        f'<span class="det-value{" det-value-long" if long else ""}">{escape(value)}</span></div>'
        for label, value, long in rows
    )
    return f'{rows_html}<div class="det-note{note_cls}">{escape(note)}</div>'


# ------------------------------------------------------------ selection (which item / day is shown)
def _open_item(prefix: str, tid: int) -> None:
    st.session_state[f"{prefix}_selected"] = tid


def _close_item(prefix: str) -> None:
    st.session_state[f"{prefix}_selected"] = None


def _open_day(prefix: str, d: date) -> None:
    st.session_state[f"{prefix}_selected_day"] = d
    st.session_state[f"{prefix}_selected"] = None


def _close_day(prefix: str) -> None:
    st.session_state[f"{prefix}_selected_day"] = None
    st.session_state[f"{prefix}_selected"] = None


def _shift(key: str, delta: int) -> None:
    st.session_state[key] = shift_month(st.session_state[key], delta)


def _go_today(key: str) -> None:
    st.session_state[key] = first_of_month(today_manila())


def _toggle_sort(key: str) -> None:
    st.session_state[key] = not st.session_state[key]


# ------------------------------------------------------------ list pieces
def render_cards(ctx: _Ctx, items: list[TransactionEntry], tab: str, top_pad: bool = True) -> None:
    """Each card is a real container with a View button, so it is clickable."""
    if top_pad:
        st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
    for r in items:
        with st.container(key=f"rcard_{tab}_{r.id}"):
            img_col, info_col, btn_col = st.columns([1.4, 6, 1.6], vertical_alignment="center")
            img_col.markdown(
                f'<div class="rc-imgwrap"><img class="rc-img" src="{escape(r.transaction.image)}"></div>',
                unsafe_allow_html=True,
            )
            info_col.markdown(card_info_html(ctx, r), unsafe_allow_html=True)
            btn_col.button("View", key=f"view_{tab}_{r.id}", on_click=_open_item,
                           args=(ctx.copy.prefix, r.id), use_container_width=True)


def sort_button(ctx: _Ctx, tab: str, asc_label: str, desc_label: str) -> None:
    """A button that just flips the order (no dropdown)."""
    state_key = ctx.key(f"asc_{tab}")
    st.button(
        asc_label if st.session_state[state_key] else desc_label,
        key=f"sort_{tab}",
        on_click=_toggle_sort,
        args=(state_key,),
        use_container_width=True,
    )


def render_calendar(ctx: _Ctx, view: date, items: list[TransactionEntry]) -> None:
    by_day = ctx.ctrl.by_day(items)
    with st.container(key="calgrid"):
        head = st.columns(7, gap="small")
        for col, n in zip(head, ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]):
            col.markdown(f'<div class="dhead">{n}</div>', unsafe_allow_html=True)

        for week in calendar.Calendar(firstweekday=6).monthdayscalendar(view.year, view.month):
            cols = st.columns(7, gap="small")
            for col, day in zip(cols, week):
                if day == 0:
                    continue
                d = date(view.year, view.month, day)
                day_items = by_day.get(d, [])
                cell_key = f"dc_today_{d:%Y%m%d}" if d == ctx.today else f"dc_{d:%Y%m%d}"
                with col:
                    with st.container(key=cell_key):
                        # invisible button covering the whole cell -> opens the day view
                        st.button(str(day), key=f"daybtn_{d:%Y%m%d}",
                                  on_click=_open_day, args=(ctx.copy.prefix, d))

                        # day number + chips go in ONE element so they can't collapse into each other
                        chips = "".join(
                            f'<div class="chip chip-{r.role.value.lower()}'
                            f'{" chip-pending" if r.status is TransactionStatus.PENDING else ""}">'
                            f'{escape(r.transaction.item)}</div>'
                            for r in day_items[:2]
                        )
                        if len(day_items) > 2:
                            chips += f'<div class="chip-more">+{len(day_items) - 2} more</div>'
                        st.markdown(
                            f'<div class="dnum">{day}</div><div class="chip-stack">{chips}</div>',
                            unsafe_allow_html=True,
                        )


def render_day_view(ctx: _Ctx, d: date, items: list[TransactionEntry]) -> None:
    """Expanded view of one calendar day, shown inside the calendar box."""
    day_items = ctx.ctrl.on_day(items, d)

    st.button("← Back to calendar", key="sort_dayback", on_click=_close_day, args=(ctx.copy.prefix,))
    st.markdown(
        f'<div class="cal-title" style="text-align:left">{d:%A, %B} {d.day}, {d.year}</div>',
        unsafe_allow_html=True,
    )
    st.caption(f"{plural(len(day_items), ctx.copy.noun)} on this day" if day_items
               else "Nothing scheduled for this day.")
    if day_items:
        render_cards(ctx, day_items, "day")


def _todo_text(ctx: _Ctx, task: TodoTask) -> tuple[str, str]:
    title, sub = ctx.copy.todo[(task.entry.role, task.step)]
    fields = {"item": task.entry.transaction.item, "name": task.entry.counterpart.name}
    return title.format(**fields), sub.format(**fields)


def render_todos(ctx: _Ctx, tasks: list[TodoTask]) -> None:
    """Each to-do is a container with an invisible button over the whole row."""
    for i, task in enumerate(tasks):
        rid = task.entry.id
        title, sub = _todo_text(ctx, task)
        with st.container(key=f"todo_{i}_{rid}"):
            st.button("Open", key=f"todobtn_{i}_{rid}", on_click=_open_item,
                      args=(ctx.copy.prefix, rid))
            st.markdown(todo_row(task.due, title, sub, ctx.today), unsafe_allow_html=True)


# ------------------------------------------------------------ dialogs
def _dialog_text(ctx: _Ctx, action: Action, r: TransactionEntry) -> str:
    fields = {"item": r.transaction.item, "name": r.counterpart.name, "dates": fmt_range(r)}
    if action is Action.ACCEPT:
        return ctx.copy.accept_text.format(**fields)
    if action is Action.REJECT:
        return ctx.copy.reject_text.format(**fields)
    if action is Action.WITHDRAW:
        return ctx.copy.withdraw_text.format(**fields)
    if action is Action.COMPLETE:
        return f"Mark “{fields['item']}” with {fields['name']} as completed? This can’t be undone."
    return f"“{fields['item']}” with {fields['name']} will be cancelled. This can’t be undone."


def _dialog_labels(ctx: _Ctx, action: Action) -> tuple[str, str]:
    """(label of the button that backs out, label of the one that confirms)."""
    return {
        Action.ACCEPT: ("Not yet", "Yes, accept"),
        Action.REJECT: ("Keep request", "Yes, reject"),
        Action.COMPLETE: ("Not yet", "Yes, complete it"),
        Action.CANCEL: (ctx.copy.keep_label, "Yes, cancel it"),
        Action.WITHDRAW: ("Keep request", "Yes, cancel it"),
    }[action]


def _perform(ctx: _Ctx, action: Action, tid: int) -> None:
    """Run the confirmed action and queue the toast the page shows next."""
    ctrl, email = ctx.ctrl, ctx.email
    result = {
        Action.ACCEPT: lambda: ctrl.accept(email, tid),
        Action.REJECT: lambda: ctrl.reject(email, tid),
        Action.WITHDRAW: lambda: ctrl.withdraw(email, tid),
        Action.COMPLETE: lambda: ctrl.complete(email, tid, ctx.today),
        Action.CANCEL: lambda: ctrl.cancel(email, tid, ctx.today),
    }[action]()
    if not result.ok:
        st.session_state[ctx.key("toast")] = result.error
        return
    item, name = result.entry.transaction.item, result.entry.counterpart.name
    st.session_state[ctx.key("toast")] = {
        Action.ACCEPT: f"Accepted {name}'s request for {item}",
        Action.REJECT: f"Rejected request for {item}",
        Action.WITHDRAW: f"Cancelled request for {item}",
        Action.COMPLETE: f"Marked {item} as completed",
        Action.CANCEL: f"Cancelled {item}",
    }[action]
    if action is Action.COMPLETE:
        st.session_state[ctx.key("review_id")] = tid   # tells the page to open the review dialog next


def _confirm_body(kind: TransactionKind, tid: int, action: Action) -> None:
    ctx = _context(kind)
    with loading("Loading...", "Couldn't load this request.", key="retry_confirm"):
        entry = ctx.ctrl.get_entry(ctx.email, tid, kind)
    if entry is None:
        st.write(NOT_FOUND_ERROR)
        return
    stem = _DIALOG_KEYS[action]
    back_label, yes_label = _dialog_labels(ctx, action)
    st.write(_dialog_text(ctx, action, entry))
    c1, c2 = st.columns(2)
    if c1.button(back_label, key=f"dlg_{stem}_no", use_container_width=True):
        st.rerun()
    if c2.button(yes_label, key=f"dlg_{stem}_yes", type="primary", use_container_width=True):
        try:
            with st.spinner("Updating..."):
                _perform(ctx, action, tid)
        except RepositoryError as exc:       # nothing was saved: keep the dialog open
            show_error(exc, "Couldn't update this request.")
            return
        st.rerun()


def _open_confirm(ctx: _Ctx, action: Action, tid: int) -> None:
    """Open the right confirmation dialog (its title depends on the action and the kind)."""
    title = {Action.COMPLETE: ctx.copy.complete_title,
             Action.CANCEL: ctx.copy.cancel_title}.get(action) or _ACTION_TITLES[action]
    st.dialog(title)(_confirm_body)(ctx.kind, tid, action)


def _review_body(kind: TransactionKind, tid: int) -> None:
    ctx = _context(kind)
    with loading("Loading...", "Couldn't load this review.", key="retry_review"):
        entry = ctx.ctrl.get_entry(ctx.email, tid, kind)
    if entry is None:
        st.write(NOT_FOUND_ERROR)
        return
    who = ctx.copy.review_who[entry.role]
    name = entry.counterpart.name
    st.write(f"How was “{entry.transaction.item}” with {name}?")

    # st.feedback returns 0-4 (index of the chosen star), or None if nothing is picked yet
    stars = st.feedback("stars", key=f"rv_stars_{tid}")
    text = st.text_area(
        "Your review (optional)",
        key=f"rv_text_{tid}",
        max_chars=500,
        placeholder=f"Share your experience with the {who}...",
    )

    c1, c2 = st.columns(2)
    if c1.button("Skip", key=f"rv_skip_{tid}", use_container_width=True):
        st.rerun()
    if c2.button("Submit review", key=f"rv_submit_{tid}", type="primary",
                 use_container_width=True, disabled=stars is None):
        try:
            with st.spinner("Submitting..."):
                result = ctx.ctrl.submit_review(ctx.email, tid, stars + 1, text)   # stars + 1 = 1-5
        except RepositoryError as exc:       # not saved: keep the dialog (and the stars) open
            show_error(exc, "Couldn't submit your review.")
            return
        st.session_state[ctx.key("toast")] = (
            f"Review for {name} submitted" if result.ok else result.error)
        st.rerun()


# ------------------------------------------------------------ details panel
def render_user_row(ctx: _Ctx, r: TransactionEntry) -> None:
    """The other person's row; clicking anywhere on it opens their profile."""
    with st.container(key=f"userrow_{r.id}"):
        st.button("View profile", key=f"userbtn_{r.id}", on_click=open_profile,
                  args=(r.counterpart.email, ctx.copy.scope))
        st.markdown(detail_user_row_html(ctx, r), unsafe_allow_html=True)


def render_actions(ctx: _Ctx, r: TransactionEntry) -> None:
    """Buttons under the details, depending on status and whether it has started."""
    tid = r.id
    actions = r.actions(ctx.today)

    if Action.ACCEPT in actions:
        # someone asked for MY listing -> I decide
        c1, c2 = st.columns(2)
        if c1.button("Accept", key="act_accept", use_container_width=True):
            _open_confirm(ctx, Action.ACCEPT, tid)
        if c2.button("Reject", key="act_reject", use_container_width=True):
            _open_confirm(ctx, Action.REJECT, tid)

    elif Action.WITHDRAW in actions:
        # I asked and they haven't answered -> I can withdraw it
        if st.button("Cancel request", key="act_cancel", use_container_width=True):
            _open_confirm(ctx, Action.WITHDRAW, tid)

    elif Action.COMPLETE in actions:
        # already started -> can be completed or cancelled
        c1, c2 = st.columns(2)
        if c1.button("Complete", key="act_complete", use_container_width=True):
            _open_confirm(ctx, Action.COMPLETE, tid)
        if c2.button("Cancel", key="act_cancel", use_container_width=True):
            _open_confirm(ctx, Action.CANCEL, tid)

    elif Action.CANCEL in actions:
        # hasn't begun yet -> can only be cancelled
        if st.button("Cancel", key="act_cancel", use_container_width=True):
            _open_confirm(ctx, Action.CANCEL, tid)


# ------------------------------------------------------------ page
def _context(kind: TransactionKind) -> _Ctx:
    return _Ctx(kind, _COPY[kind], get_transaction_controller(), get_current_email(), today_manila())


def _init_state(ctx: _Ctx) -> None:
    ss = st.session_state
    if ctx.key("month") not in ss:
        ss[ctx.key("month")] = first_of_month(ctx.today)
    # True = oldest/soonest first, False = newest/latest first
    ss.setdefault(ctx.key("asc_mine"), True)
    ss.setdefault(ctx.key("asc_pending"), True)
    ss.setdefault(ctx.key("asc_done"), False)
    ss.setdefault(ctx.key("asc_cancel"), False)
    ss.setdefault(ctx.key("selected"), None)       # id shown in the details panel
    ss.setdefault(ctx.key("selected_day"), None)   # day shown in the expanded calendar view


def _tab_header(ctx: _Ctx, asc_label: str, desc_label: str, tab: str, filters: dict, key: str):
    """Filter pills + sort button of the Pending / Completed / Cancelled tabs.
    Returns the picked filter label (None = show everything)."""
    filt_col, sort_col = st.columns([4.726, 1.274], vertical_alignment="center")
    with filt_col:
        chosen = st.pills("Filter", list(filters), selection_mode="single",
                          label_visibility="collapsed", key=key)
    with sort_col:
        sort_button(ctx, tab, asc_label, desc_label)
    return chosen


def _render_list(ctx: _Ctx, items: list[TransactionEntry], tab: str, empty: str) -> None:
    with st.container(height=LIST_H, border=False):
        if items:
            render_cards(ctx, items, tab)
        else:
            st.caption(empty)


def _tab_mine(ctx: _Ctx, entries: list[TransactionEntry]) -> None:
    """Calendar or list of accepted ones."""
    ss, copy = st.session_state, ctx.copy
    view_col, filt_col, _, sort_col = st.columns([1.1, 1.9, 1.7, 1.3], vertical_alignment="center")
    with view_col:
        view_mode = st.pills(
            "View", ["Calendar", "List"], default="Calendar",
            label_visibility="collapsed", key="pills_view",
        ) or "Calendar"
    with filt_col:
        chosen = st.pills(
            "Filter", list(copy.mine_filters), selection_mode="single",
            label_visibility="collapsed", key="pills_mine",
        )

    # nothing selected -> show everything
    items = ctx.ctrl.active(entries, copy.mine_filters.get(chosen))

    if view_mode == "Calendar":
        view = ss[ctx.key("month")]
        with st.container(height=CAL_H, border=False):
            if ss[ctx.key("selected_day")] is not None:
                render_day_view(ctx, ss[ctx.key("selected_day")], items)
            else:
                month_key = ctx.key("month")
                with st.container(key="nav_mine"):
                    prev_col, title_col, next_col, today_col = st.columns(
                        [1, 4, 1, 2], vertical_alignment="center"
                    )
                    prev_col.button("‹", key=f"{copy.prefix}_prev", on_click=_shift,
                                    args=(month_key, -1), use_container_width=True)
                    title_col.markdown(f'<div class="cal-title">{view:%B %Y}</div>', unsafe_allow_html=True)
                    next_col.button("›", key=f"{copy.prefix}_next", on_click=_shift,
                                    args=(month_key, 1), use_container_width=True)
                    today_col.button("Today", key=f"{copy.prefix}_today", on_click=_go_today,
                                     args=(month_key,), use_container_width=True)

                render_calendar(ctx, view, items)
                (first_role, first_text), (second_role, second_text) = copy.legend
                st.markdown(
                    '<div class="cal-legend">'
                    f'<span class="dot dot-{first_role.value.lower()}"></span>{escape(first_text)}'
                    f'<span class="dot dot-{second_role.value.lower()}"></span>{escape(second_text)}'
                    '</div>',
                    unsafe_allow_html=True,
                )
    else:
        with sort_col:
            sort_button(ctx, "mine", "↑ Soonest first", "↓ Latest first")
        items = ctx.ctrl.sort_by_start(items, ss[ctx.key("asc_mine")])
        with st.container(height=LIST_H, border=False):
            if items:
                render_cards(ctx, items, "mine")
            else:
                st.caption(copy.empty_mine)


def _tab_pending(ctx: _Ctx, entries: list[TransactionEntry]) -> None:
    chosen = _tab_header(ctx, "↑ Soonest first", "↓ Latest first", "pending",
                         PENDING_FILTERS, "pills_pending")
    items = ctx.ctrl.pending(entries, PENDING_FILTERS.get(chosen))
    items = ctx.ctrl.sort_by_start(items, st.session_state[ctx.key("asc_pending")])
    _render_list(ctx, items, "pending", "No pending requests.")


def _tab_done(ctx: _Ctx, entries: list[TransactionEntry]) -> None:
    chosen = _tab_header(ctx, "↑ Oldest first", "↓ Newest first", "done",
                         ctx.copy.done_filters, "pills_done")
    items = ctx.ctrl.completed(entries, ctx.copy.done_filters.get(chosen))
    items = ctx.ctrl.sort_by_end(items, st.session_state[ctx.key("asc_done")])
    _render_list(ctx, items, "done", ctx.copy.empty_done)


def _tab_cancel(ctx: _Ctx, entries: list[TransactionEntry]) -> None:
    chosen = _tab_header(ctx, "↑ Oldest first", "↓ Newest first", "cancel",
                         CANCELLED_FILTERS, "pills_cancel")
    items = ctx.ctrl.cancelled(entries, CANCELLED_FILTERS.get(chosen))
    items = ctx.ctrl.sort_by_start(items, st.session_state[ctx.key("asc_cancel")])
    _render_list(ctx, items, "cancel", ctx.copy.empty_cancel)


def _render_right(ctx: _Ctx, entries: list[TransactionEntry]) -> None:
    """Details of the picked one (replaces the to-do list), or the to-do summary."""
    selected = ctx.ctrl.get_entry(ctx.email, st.session_state[ctx.key("selected")], ctx.kind)

    if selected is not None:
        st.subheader(ctx.copy.details_title)
        st.caption("Press Back to return to your to-do list.")
        with st.container(height=TODO_H, border=False):
            # the "sort_" key prefix reuses the pill-button style
            st.button("← Back to To-Do", key="sort_back", on_click=_close_item,
                      args=(ctx.copy.prefix,))
            with st.container(key="detail_panel"):
                st.markdown(detail_top_html(selected), unsafe_allow_html=True)
                render_user_row(ctx, selected)
                st.markdown(detail_bottom_html(ctx, selected), unsafe_allow_html=True)
                st.markdown('<div style="height:0.8rem"></div>', unsafe_allow_html=True)
                render_actions(ctx, selected)
    else:
        st.subheader("To-Do")
        tasks = ctx.ctrl.todos(entries, ctx.today)
        overdue = ctx.ctrl.overdue_count(tasks, ctx.today)
        st.caption(
            f"{len(tasks)} open task(s)" + (f" · {overdue} overdue" if overdue else "")
        )

        with st.container(height=TODO_H, border=False):
            if tasks:
                render_todos(ctx, tasks)
            else:
                st.caption("You're all caught up.")


def render_transactions(kind: TransactionKind) -> None:
    """Draw the whole Gigs or Rentals page."""
    copy = _COPY[kind]
    if render_open_profile(copy.scope):
        st.stop()

    load_css("transactions")
    ctx = _context(kind)
    _init_state(ctx)
    review_id = st.session_state.get(ctx.key("review_id"))
    with loading(f"Loading your {copy.title.lower()}...", f"Couldn't load your {copy.title}.",
                 key=f"retry_{copy.prefix}_load"):
        entries = ctx.ctrl.entries(ctx.email, kind)
        offer_review = review_id is not None and ctx.ctrl.can_review(ctx.email, review_id)

    # After "Yes, complete it", open the review dialog once.
    # pop() clears the flag, so closing the dialog with the X won't make it reappear
    # (and a failed load above leaves it set, so the review is still offered on retry).
    st.session_state.pop(ctx.key("review_id"), None)
    if offer_review:
        st.dialog("Leave a review")(_review_body)(kind, review_id)

    if ctx.key("toast") in st.session_state:
        st.toast(st.session_state.pop(ctx.key("toast")))

    with st.container(key="page_header"):
        st.title(copy.title)
        st.caption(copy.caption)

    left_col, divider_col, right_col = st.columns([2, 0.06, 1], gap="small")

    with divider_col:
        st.markdown(
            f'<div class="vdivider" style="height:{DIVIDER_H}px"></div>',
            unsafe_allow_html=True,
        )

    with left_col:
        tab_mine, tab_pending, tab_done, tab_cancel = st.tabs(
            [copy.mine_tab, "Pending", "Completed", "Cancelled"]
        )
        with tab_mine:
            _tab_mine(ctx, entries)
        with tab_pending:
            _tab_pending(ctx, entries)
        with tab_done:
            _tab_done(ctx, entries)
        with tab_cancel:
            _tab_cancel(ctx, entries)

    with right_col:
        _render_right(ctx, entries)