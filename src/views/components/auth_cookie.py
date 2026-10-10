"""A6: the browser cookie that keeps a person signed in across a page refresh.

Why a cookie: Streamlit's session_state is wiped by a browser refresh (F5). The decision
from the A1 spike:
  * READ  the cookie on the server with st.context.cookies. It holds what the browser
    sent when this page was loaded, so a cookie written during this visit is only
    visible after the next refresh. That is exactly the moment we need it.
  * WRITE it with one line of JavaScript in a hidden iframe (the server cannot set
    cookies in Streamlit).
What is stored: ONLY the Supabase refresh token (never the access token or password),
Path=/, SameSite=Lax, 30 days, Secure when the page is https. JavaScript writes it, so it
cannot be HttpOnly: accepted for a school project (see the handoff, A1).

Writing is queued in session_state and sent by flush_cookie_command(), called once per
run by App.py. It cannot be sent right before st.rerun(): the rerun would replace the
page before the browser ran the script.
"""
import json
from urllib.parse import unquote

import streamlit as st

COOKIE_NAME = "sh_refresh"
COOKIE_DAYS = 30
_COMMAND_KEY = "_cookie_command"        # ("write", token) or ("clear", None)


def read_refresh_cookie() -> str | None:
    """The refresh token the browser sent with this page load, or None."""
    try:
        value = st.context.cookies.get(COOKIE_NAME)
    except Exception:
        return None
    return unquote(value) if value else None


def queue_cookie_write(refresh_token: str) -> None:
    """Remember this refresh token in the browser (sent on the next flush)."""
    st.session_state[_COMMAND_KEY] = ("write", refresh_token)


def queue_cookie_clear() -> None:
    """Forget the saved login in the browser (sent on the next flush)."""
    st.session_state[_COMMAND_KEY] = ("clear", None)


def _script(action: str, token: str | None) -> str:
    # a safe JavaScript string literal ("</" is escaped so it can never close the script tag)
    value = json.dumps(token or "").replace("</", "<\\/")
    max_age = COOKIE_DAYS * 86400 if action == "write" else 0
    return f"""<script>
(function () {{
  try {{
    var secure = window.location.protocol === 'https:' ? '; Secure' : '';
    document.cookie = '{COOKIE_NAME}=' + encodeURIComponent({value}) +
      '; Path=/; SameSite=Lax; Max-Age={max_age}' + secure;
  }} catch (e) {{}}
}})();
</script>"""


def flush_cookie_command() -> None:
    """Send the queued cookie change to the browser (a hidden 1px iframe), once."""
    command = st.session_state.pop(_COMMAND_KEY, None)
    if not command:
        return
    html = _script(*command)
    if hasattr(st, "iframe"):                   # Streamlit 1.65+
        st.iframe(html, height=1)
    else:                                       # older Streamlit; deprecated there later
        import streamlit.components.v1 as components
        components.html(html, height=0)
