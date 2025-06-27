import os
import streamlit as st

import common.session.authentication as auth
from src.session import control
from common.logging.st_logger import st_logger


def start_app():
    """
    Function to start the chat application.

    This function sets the app page configuration, checks if the guest mode is enabled or authentication is required,
    initializes a new session if necessary, and starts the chat feature in the current session.

    Parameters:
        None

    Returns:
        None

    Influenced Session State Variables:
        - st.session_state.guest_mode
        - st.session_state.authenticated
        - st.session_state.session

    """

    # Set chat_app main page
    st.set_page_config(
        page_title="FEI STU Chat",
        page_icon="💬",
        layout="centered",
        initial_sidebar_state="auto",
    )

    st_logger.debug("debugging")

    # ON LOCALHOST: please add GUEST_MODE variable to your local .env
    # GUEST_MODE=1 -> guest mode enable
    # GUEST_MODE=0 -> authentication enabled
    if "guest_mode" not in st.session_state:
        st.session_state.guest_mode = os.getenv("GUEST_MODE")

    if st.session_state.guest_mode == "1":
        auth.enable_guest_mode()
    else:
        auth.authenticate_user()

    # If user log in successfully
    if st.session_state.authenticated:

        # If any session is not initialized, initialize new session
        if "session" not in st.session_state:
            control.new_session(
                0, st.session_state.user_id, st.session_state.session_lang, False
            )
            st_logger.info("New session initialized")

        # Start chat feature in current session
        st.session_state.session.chat()


# Main function call for chat_app
if __name__ == "__main__":

    start_app()
