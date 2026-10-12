"""A6: the browser cookie that keeps a person signed in across a page refresh.

What is stored: ONLY the Supabase refresh token (never the access token or password),
Path=/, SameSite=Lax, 30 days, Secure when the page is https. JavaScript writes it, so it
cannot be HttpOnly: accepted for a school project (see the handoff, A1).

READING. Two ways, tried in this order:
  1. st.context.cookies: what the browser sent when the page loaded. Instant, but Streamlit
     Community Cloud's proxy removes cookies from that request, so on Cloud it is always empty.
  2. A small st.components.v2 component whose JavaScript reads document.cookie in the browser
     and reports it back (one extra rerun right after the page loads). This works everywhere.
read_refresh_cookie() returns COOKIE_PENDING until the browser has answered.

WRITING. Queued in session_state and sent by flush_cookie_command() once per run (App.py calls
it at the end). A write queued just before st.rerun() is therefore sent by the next run.
"""
from uuid import uuid4

import streamlit as st

COOKIE_NAME = "sh_refresh"
COOKIE_DAYS = 30

_COMMAND_KEY = "_cookie_command"        # ("write", token) or ("clear", None)
_SID_KEY = "_cookie_sid"                # this browser session's id, echoed back by the component
_SEEN_KEY = "_cookie_seen"              # what the browser reported (token string, or None)
_READER_KEY = "sh_cookie_reader"
_WRITER_KEY = "sh_cookie_writer"


class _Pending:
    def __repr__(self) -> str:
        return "COOKIE_PENDING"


COOKIE_PENDING = _Pending()             # "the browser has not told us yet"

# Runs in the app page (not an iframe), so document.cookie is the app's own cookie jar.
# Each piece is guarded by an id so a rerun never repeats it.
_JS = """
export default function (component) {
  const { data, setStateValue } = component;
  const NAME = '%(name)s';

  function readCookie() {
    try {
      const parts = document.cookie ? document.cookie.split('; ') : [];
      for (const part of parts) {
        const i = part.indexOf('=');
        if (part.slice(0, i) === NAME) return decodeURIComponent(part.slice(i + 1));
      }
    } catch (e) {}
    return '';
  }

  function writeCookie(value, maxAge) {
    try {
      const secure = window.location.protocol === 'https:' ? '; Secure' : '';
      document.cookie = NAME + '=' + encodeURIComponent(value) +
        '; Path=/; SameSite=Lax; Max-Age=' + maxAge + secure;
    } catch (e) {}
  }

  const cmd = data && data.command;
  if (cmd && window.__shCookieLastCommand !== cmd.id) {
    window.__shCookieLastCommand = cmd.id;
    if (cmd.action === 'write') writeCookie(cmd.token, cmd.max_age);
    else writeCookie('', 0);
  }

  if (data && data.sid && window.__shCookieSid !== data.sid) {
    window.__shCookieSid = data.sid;
    setStateValue('read', { sid: data.sid, token: readCookie() });
  }
}
""" % {"name": COOKIE_NAME}

try:
    _bridge = st.components.v2.component("sh_cookie_bridge", js=_JS)
except Exception:                       # older Streamlit without components v2
    _bridge = None


def _mount(key: str, data: dict):
    return _bridge(data=data, key=key, on_read_change=lambda: None)


def read_refresh_cookie():
    """The saved refresh token (str), None when there is none, or COOKIE_PENDING while the
    browser has not answered yet (the caller waits; the answer arrives on the next rerun)."""
    ss = st.session_state
    if _SEEN_KEY in ss:
        return ss[_SEEN_KEY]

    # 1. the cookie the browser sent with the page (works on localhost and normal hosts)
    try:
        sent = st.context.cookies.get(COOKIE_NAME)
    except Exception:
        sent = None
    if sent:
        ss[_SEEN_KEY] = _unquote(sent)
        return ss[_SEEN_KEY]

    # 2. ask the browser (needed on Streamlit Community Cloud)
    if _bridge is None:
        ss[_SEEN_KEY] = None
        return None
    sid = ss.setdefault(_SID_KEY, uuid4().hex)
    result = _mount(_READER_KEY, {"sid": sid})
    reported = result.read
    if isinstance(reported, dict) and reported.get("sid") == sid:
        ss[_SEEN_KEY] = reported.get("token") or None
        return ss[_SEEN_KEY]
    return COOKIE_PENDING


def _unquote(value: str) -> str:
    from urllib.parse import unquote
    return unquote(value)


def queue_cookie_write(refresh_token: str) -> None:
    """Remember this refresh token in the browser (sent on the next flush)."""
    st.session_state[_COMMAND_KEY] = ("write", refresh_token)


def queue_cookie_clear() -> None:
    """Forget the saved login in the browser (sent on the next flush)."""
    st.session_state[_COMMAND_KEY] = ("clear", None)


def flush_cookie_command() -> None:
    """Send the queued cookie change to the browser, once."""
    command = st.session_state.pop(_COMMAND_KEY, None)
    if not command or _bridge is None:
        return
    action, token = command
    _mount(_WRITER_KEY, {"command": {
        "id": uuid4().hex,
        "action": action,
        "token": token or "",
        "max_age": COOKIE_DAYS * 86400,
    }})
