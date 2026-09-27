import streamlit as st
from streamlit_calendar import calendar

def render():

    st.header("Welcome, User!")
    st.subheader("Here’s what’s happening in your hive today.")

    st.divider()

    left_col, right_col = st.columns([2, 1])

    # ==========================================
    # LEFT SIDE (2/3) - CALENDAR
    # ==========================================

    with left_col:

        st.subheader("Calendar")

        calendar_options = {
            "editable": True,
            "selectable": True,
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek,timeGridDay"
            },
            "initialView": "dayGridMonth",
            "height": 550,  # 👈 controls overall calendar height in pixels
        }

        calendar_events = [
            {
                "title": "Sample Event",
                "start": "2026-09-28",
                "end": "2026-09-29",
            },
        ]

        calendar(
            events=calendar_events,
            options=calendar_options,
            key="dashboard_calendar"
        )

    # ==========================================
    # RIGHT SIDE (1/3) - TOP/BOTTOM SPLIT
    # ==========================================

    with right_col:

        top_row = st.container(border=True)
        bottom_row = st.container(border=True)

        with top_row:
            st.subheader("Upcoming")
            st.write("Content goes here.")
            st.write("Content goes here.")
            st.write("Content goes here.")

        with bottom_row:
            st.subheader("Notifications")
            st.write("Content goes here.")
            st.write("Content goes here.")
            