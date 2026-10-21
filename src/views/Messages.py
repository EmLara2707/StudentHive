"""Messages page: a PREVIEW of the inbox. Nothing here is saved or sent.

The conversations below are placeholder text so the page is not empty. Clicking a
conversation switches the chat on the right, and Send only shows a "coming soon" note.
Real messaging (storage, realtime, unread counts) is not built yet.
Styles: views/styles/messages.css.
"""
from html import escape

import streamlit as st

from views.components.styles import load_css

# NOTE: do NOT call st.set_page_config here. App.py already does it.

# ---------- placeholder content (not real people, not stored anywhere) ----------
# Each message: (who, text, time) where who is "them" or "me".
SAMPLE_CHATS = [
    {
        "name": "Sample Student A", "time": "9:41 AM", "online": True,
        "item": "Logo design for your org", "price": "₱300/hr",
        "messages": [
            ("them", "Hi! Is this still available for next week?", "9:30 AM"),
            ("me", "Yes, it is. What date works for you?", "9:35 AM"),
            ("them", "Thursday afternoon would be great.", "9:41 AM"),
        ],
    },
    {
        "name": "Sample Student B", "time": "Yesterday", "online": False,
        "item": "Camera rental", "price": "₱250/day",
        "messages": [
            ("them", "Can I pick up the camera at the library?", "4:02 PM"),
            ("me", "Sure, around 10 AM works for me.", "4:10 PM"),
        ],
    },
    {
        "name": "Sample Student C", "time": "Mon", "online": False,
        "item": "Math tutoring", "price": "₱150/hr",
        "messages": [
            ("them", "Thanks for the session!", "6:15 PM"),
            ("me", "Anytime. Good luck on the exam!", "6:20 PM"),
        ],
    },
    {
        "name": "Sample Student D", "time": "Oct 12", "online": True,
        "item": "Project poster layout", "price": "₱500",
        "messages": [("them", "I sent over the project details.", "2:00 PM")],
    },
    {
        "name": "Sample Student E", "time": "Oct 9", "online": False,
        "item": "Tripod rental", "price": "₱80/day",
        "messages": [("me", "Hi! Is the tripod free this weekend?", "11:12 AM")],
    },
]


# ------------------------------------------------------------ html builders
def _avatar(name: str, cls: str = "") -> str:
    return f'<div class="msg-avatar {cls}">{escape(name[-1:].upper())}</div>'


def _preview(chat: dict) -> str:
    who, text, _ = chat["messages"][-1]
    return ("You: " if who == "me" else "") + text


def convo_row_html(chat: dict, selected: bool) -> str:
    return (
        f'<div class="msg-row{" msg-row-sel" if selected else ""}">'
        f'{_avatar(chat["name"])}'
        '<div class="msg-row-info">'
        f'<div class="msg-row-name">{escape(chat["name"])}</div>'
        f'<div class="msg-row-text">{escape(_preview(chat))}</div>'
        '</div>'
        f'<div class="msg-row-time">{escape(chat["time"])}</div>'
        '</div>'
    )


def chat_header_html(chat: dict) -> str:
    status = ('<div class="msg-online">Online</div>' if chat["online"]
              else '<div class="msg-offline">Offline</div>')
    return (
        '<div class="msg-head">'
        f'{_avatar(chat["name"], "msg-avatar-lg")}'
        f'<div><div class="msg-head-name">{escape(chat["name"])}</div>{status}</div>'
        '</div>'
        '<div class="msg-item">'
        '<div class="msg-thumb"></div>'
        f'<div><div class="msg-item-title">{escape(chat["item"])}</div>'
        f'<div class="msg-item-price">{escape(chat["price"])}</div></div>'
        '</div>'
    )


def bubbles_html(chat: dict) -> str:
    out = ['<div class="msg-day">Today</div>']
    for who, text, when in chat["messages"]:
        side = "me" if who == "me" else "them"
        avatar = "" if who == "me" else _avatar(chat["name"], "msg-avatar-sm")
        out.append(
            f'<div class="msg-line msg-line-{side}">{avatar}'
            f'<div><div class="msg-bubble msg-bubble-{side}">{escape(text)}</div>'
            f'<div class="msg-time">{escape(when)}</div></div></div>'
        )
    return "".join(out)


# ------------------------------------------------------------ callbacks
def _open_chat(index: int) -> None:
    st.session_state.msg_selected = index


def _send() -> None:
    """Placeholder: nothing is sent or stored."""
    st.session_state.msg_toast = "Messaging is coming soon. This is a preview."
    st.session_state.msg_draft = ""


# ------------------------------------------------------------ page
load_css("messages")
st.session_state.setdefault("msg_selected", 0)
st.session_state.setdefault("msg_draft", "")
if "msg_toast" in st.session_state:
    st.toast(st.session_state.pop("msg_toast"))

selected = min(st.session_state.msg_selected, len(SAMPLE_CHATS) - 1)
chat = SAMPLE_CHATS[selected]

st.caption("Preview only: these conversations are samples, and nothing you type is sent.")

list_col, chat_col = st.columns([1, 1.6], gap="small")

with list_col:
    with st.container(key="msg_list_box"):
        st.markdown('<div class="msg-title">Messages</div>', unsafe_allow_html=True)
        st.text_input("Search messages", placeholder="Search messages", key="msg_search",
                      label_visibility="collapsed", disabled=True)
        for i, c in enumerate(SAMPLE_CHATS):
            with st.container(key=f"convo_{i}"):
                st.button("Open", key=f"convobtn_{i}", on_click=_open_chat, args=(i,))
                st.markdown(convo_row_html(c, i == selected), unsafe_allow_html=True)

with chat_col:
    with st.container(key="msg_chat_box"):
        st.markdown(chat_header_html(chat), unsafe_allow_html=True)
        with st.container(height=360, border=False, key="msg_thread"):
            st.markdown(bubbles_html(chat), unsafe_allow_html=True)
        with st.container(key="msg_compose", horizontal=True, vertical_alignment="center"):
            st.text_input("Message", placeholder="Type a message...", key="msg_draft",
                          label_visibility="collapsed")
            st.button("➤", key="msg_send", on_click=_send)
