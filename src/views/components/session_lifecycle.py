"""A6: session lifecycle: restore a login after a refresh, keep the access token fresh,
and sign out cleanly. App.py calls these; the rules live in AuthController.

Two rules from the A1 spike:
  * Supabase refresh tokens are single-use. So the refresh happens in exactly TWO places
    (restore_login_on_load and keep_tokens_fresh), and each stores the NEW token
    (session_state and cookie) straight away.
  * If a refresh fails for good, the cookie is cleared and the login page shows
    "Your session expired".
"""
import streamlit as st

from utils.token_expiry import seconds_left
from views.components.auth_cookie import (
    COOKIE_PENDING, queue_cookie_clear, queue_cookie_write, read_refresh_cookie,
)
from views.session import (
    end_session, get_auth_controller, get_auth_tokens, start_session, store_auth_tokens,
)

REFRESH_BEFORE_SECONDS = 120          # renew the access token when under 2 minutes are left
_TRIED_KEY = "restore_tried"          # once per browser session: never refresh twice
_NOTICE_KEY = "session_notice"        # message for the login page


def restore_login_on_load() -> None:
    """On the first run of a browser session with nobody logged in: if the cookie holds
    a refresh token, sign that person back in."""
    if st.session_state.get("logged_in") or st.session_state.get(_TRIED_KEY):
        return
    auth = get_auth_controller()
    token = read_refresh_cookie()
    if token is COOKIE_PENDING:
        _wait_for_browser()                         # does not return (st.stop)
    st.session_state[_TRIED_KEY] = True
    if not token:
        return

    with st.spinner("Restoring your session..."):
        result = auth.restore(token)

    if result.ok:
        store_auth_tokens(*result.tokens)
        queue_cookie_write(result.tokens[1])        # the old token is spent: save the new one
        start_session(result.user)
    elif result.can_retry:
        # Only the network failed, so the saved login is still good. Keep the cookie.
        st.session_state[_NOTICE_KEY] = "Couldn't reach the server. Refresh the page to try again."
    else:
        queue_cookie_clear()
        st.session_state[_NOTICE_KEY] = result.error


def _wait_for_browser() -> None:
    """The browser has not reported its cookie yet (it answers within a moment, then the page
    reruns by itself). Show a short message and stop. If it never answers (script blocked),
    a button appears after a few seconds so nobody is stuck here."""
    st.markdown(
        "<style>.st-key-cookie_wait_skip { opacity: 0; animation: shShow 0s 6s forwards; }"
        "@keyframes shShow { to { opacity: 1; } }</style>",
        unsafe_allow_html=True,
    )
    st.caption("Loading...")
    if st.button("Taking too long? Go to the login page", key="cookie_wait_skip"):
        st.session_state[_TRIED_KEY] = True
        st.rerun()
    st.stop()


def keep_tokens_fresh() -> None:
    """While logged in with Supabase: renew the access token (valid 1 hour) shortly before
    it expires. The clients do not refresh by themselves (auto_refresh_token=False)."""
    if not st.session_state.get("logged_in"):
        return
    tokens = get_auth_tokens()
    if not tokens:
        return                                       # no tokens stored: nothing to renew
    left = seconds_left(tokens[0])
    if left is None or left > REFRESH_BEFORE_SECONDS:
        return

    result = get_auth_controller().renew_tokens(tokens)
    if result.ok:
        store_auth_tokens(*result.tokens)
        queue_cookie_write(result.tokens[1])
    elif not result.can_retry:                       # network blips: try again on the next run
        sign_out_everywhere(notice=result.error)
        st.rerun()


def sign_out_everywhere(notice: str | None = None) -> None:
    """end_session() plus forgetting the saved login. Use this instead of end_session()
    in views, otherwise the cookie would log the person straight back in on refresh."""
    end_session()
    # st.context.cookies still shows the cookie this page was loaded with, so mark the
    # restore as already tried or the next run would sign the person back in.
    st.session_state[_TRIED_KEY] = True
    queue_cookie_clear()
    if notice:
        st.session_state[_NOTICE_KEY] = notice


def pop_session_notice() -> str | None:
    """The 'session expired' style message for the login page, shown once."""
    return st.session_state.pop(_NOTICE_KEY, None)
