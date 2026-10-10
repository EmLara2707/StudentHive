"""Spinner + friendly error for slow or failing storage calls (B5).

Repositories raise RepositoryError (never a raw database exception) and its message is
safe to show a student. Views use these helpers so a failed call shows a plain message
and a "Try again" button instead of Streamlit's red traceback.

    with loading("Loading your gigs...", "Couldn't load your gigs.", key="retry_gigs"):
        entries = controller.entries(...)

- loading(): spinner while the block runs. If it raises RepositoryError, show the error
  with a "Try again" button and stop this script run (st.stop), so the code after the
  block never sees missing data. Inside a dialog this stops only that dialog.
- show_error(): just draw the message, for places that handle the failure themselves
  (a form submit that must keep the person's input on screen).

Streamlit's own control-flow exceptions (st.rerun, st.stop) are not RepositoryErrors,
so they pass straight through.
"""
from contextlib import contextmanager

import streamlit as st

from repositories.errors import RepositoryError


def show_error(exc: RepositoryError, context: str = "", retry_key: str | None = None) -> None:
    """Friendly message: what failed, then why (the repository's own safe text).
    With retry_key, add a "Try again" button; any click re-runs the script."""
    st.error(f"{context} {exc}".strip())
    if retry_key:
        st.button("Try again", key=retry_key)


@contextmanager
def loading(text: str, error_context: str, key: str):
    """Spinner while the block runs; on RepositoryError show the error and stop."""
    try:
        with st.spinner(text):
            yield
    except RepositoryError as exc:
        show_error(exc, error_context, retry_key=key)
        st.stop()
