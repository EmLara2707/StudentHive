import streamlit as st

def render():

    st.header("Welcome, User!")
    st.subheader("Here’s what’s happening in your hive today.")

    st.divider()

    left_col, right_col = st.columns([2, 1])

    # ==========================================
    # LEFT SIDE (2/3) - CALENDAR
    # ==========================================

    with left_col:

        st.subheader("Listings")

        listings = [
            {
                "image": "https://via.placeholder.com/150",
                "name": "Math Tutoring",
                "label": "Gig",
                "price": "₱150/hr",
            },
            {
                "image": "https://via.placeholder.com/150",
                "name": "Studio Apartment",
                "label": "Rental",
                "price": "₱8,000/mo",
            },
            {
                "image": "https://via.placeholder.com/150",
                "name": "Dog Walking",
                "label": "Gig",
                "price": "₱100/hr",
            },
            {
                "image": "https://via.placeholder.com/150",
                "name": "Cleaning",
                "label": "Gig",
                "price": "₱100/hr",
            },
        ]

        with st.container(height=600, border=True):

            for item in listings:

                with st.container(border=True):

                    img_col, info_col = st.columns([1, 2])

                    with img_col:
                        st.image(item["image"], use_container_width=True)

                    with info_col:
                        st.markdown(f"**{item['name']}**")
                        st.caption(item["label"])
                        st.write(item["price"])
    # ==========================================
    # RIGHT SIDE (1/3) - TOP/BOTTOM SPLIT
    # ==========================================

    with right_col:
        st.subheader("")
        top_row = st.container(border=True)
        bottom_row = st.container(border=True)

        with top_row:
            st.subheader("Gigs")
            st.write("Content goes here.")
            st.write("Content goes here.")
            st.write("Content goes here.")

        with bottom_row:
            st.subheader("Rentals")
            st.write("Content goes here.")
            st.write("Content goes here.")
            