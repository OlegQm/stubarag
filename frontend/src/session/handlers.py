import datetime

import streamlit as st

"""

A module for handling various errors and exceptions in the session package.

!!! THIS MODULE IS WORK IN PROGRESS !!!

"""


# Generates timestamp for logging
def timestamp() -> str:
    """
    Generates a timestamp in the format "dd-mm-yyyy_hh-mm-ss".

    Args:
        None

    Returns:
        str: The generated timestamp.

    """
    now = datetime.datetime.now()
    date_time = now.strftime("%d-%m-%Y_%H-%M-%S")

    return date_time


# Handler when connection to OpenAI API fails
def lost_API_connection() -> None:
    """
    Function to handle the case of a lost API connection.

    Streamlit is stopped after lost API connection.
    Reload of page is needed.

    Args:
        None

    Returns:
        None

    """

    st.error("Chyba spojenia s LLM")
    st.stop()


# Handler when API key is missing
def missing_API_key() -> None:
    """
    Function to handle missing API key error.

    Displays an error message and provides an option to retry the connection.

    Args:
        None

    Returns:
        None

    """

    st.error("Chyba spojenia s LLM")
    spacer1, col, spacer2 = st.columns([1, 2, 1])

    with col:
        if st.button("Skúsiť znova", use_container_width=True):
            st.rerun()

    st.stop()
