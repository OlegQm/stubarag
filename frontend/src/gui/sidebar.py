import streamlit as st

import common.session.authentication as auth
from src.gui import style
from src.session import control, history_menu

"""

A module for creating the sidebar layout for the chat application.

"""


# Function that creates sidebar:
def create(user_id: str) -> None:
    """
    Creates the sidebar for the chat application GUI.
    This function sets up the sidebar with various buttons and elements, including:

    Args:
        - user_id (str): The ID of the current user.

    Returns:
        None

    Layout:
        - A logout button.
        - Language switching buttons for Slovak and English.
        - A button to start a new conversation.
        - Optionally, a section for displaying conversation history if history is enabled.

    """

    style.apply_style_sidebar()

    with st.sidebar:

        # Create buttons for language switching
        spacer1, col1, spacer2 = st.columns(
            [0.5, 1, 0.5], gap="small", vertical_alignment="center"
        )

        with col1:
            st.button(
                st.session_state.translator("Log out"),
                key="logout",
                type="secondary",
                on_click=auth.logout,
                use_container_width=True,
                disabled=(True if st.session_state.guest_mode == "1" else False),
            )

        # Create buttons for language switching
        spacer1, col1, col2, spacer2 = st.columns(
            [1.5, 1.3, 1.3, 1.5], gap="small", vertical_alignment="center"
        )

        with col1:
            st.button(
                "SK",
                help="Slovenčina",
                on_click=control.set_language,
                args=("sk",),
                type="primary",
                key="slovak",
                use_container_width=True,
            )

        with col2:
            st.button(
                "EN",
                help="English",
                on_click=control.set_language,
                args=("en",),
                type="primary",
                key="english",
                use_container_width=True,
            )

        # Just a spacer
        st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)

        # Create button for starting a new conversation
        spacer1, col, spacer2 = st.columns([0.25, 1, 0.25])
        with col:

            st.button(
                st.session_state.translator("New Conversation"),
                on_click=control.new_conversation,
                args=(
                    (st.session_state.run_id + 1),
                    user_id,
                    st.session_state.session_lang,
                    False,
                ),
                use_container_width=True,
            )

        if st.session_state.history_enabled:
            # Just a spacer
            st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)

            style.create_sidebar_header(
                st.session_state.translator("Conversation History")
            )

            spacer1, col, spacer2 = st.columns([0.05, 1, 0.05])
            with col:

                history_menu.display(user_id)
