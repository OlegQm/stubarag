import gettext
import streamlit as st
import logging

import common.session.authentication as auth

from streamlit import runtime
from streamlit.runtime.scriptrunner import get_script_run_ctx

from src.session import history_menu, main_session

"""

A module for session control functions.

"""


# Callback function for "Nová konverzácia" button
# Initiate new session
def new_session(run_id: int, user_id: str, language: str, historical: bool) -> bool:
    """
    Creates a new session object and assigns it to the session_state.session variable.

    Args:
        - run_id (int): The ID of the session run.
        - user_id (str): The ID of the user.
        - language (str): The language used in the session.
        - historical (bool): Indicates whether the session is loaded from history or not.

    Returns:
        - bool: True if the session object is created successfully, False otherwise.

    Influenced Session State Variables:
        - st.session_state.session
        - st.session_state.emphasis
        - st.session_state.rec_id

    """
    try:
        # Initialize new Session object
        st.session_state.session = main_session.Session(
            run_id, user_id, language, historical
        )
        return True

    except Exception:
        print("A Session object encountered an error")
        return False


# Function that starts new conversation
def new_conversation(
    run_id: int, user_id: str, language: str, historical: bool, no: int = 0
) -> main_session.Session:
    """
    Start a new conversation. A wrapper function for the new_session function.

    This function is used in history menu for conversation switching.

    Args:
        - run_id (int): The ID of the run.
        - user_id (str): The ID of the user.
        - language (str): The language of the conversation.
        - historical (bool): Indicates if the conversation is loaded from history or not.
        - no (int, optional): The order of the conversation in the history menu. Defaults to 0.

    Returns:
        - main_session.Session: The Session object - instance of Session class.

    Influenced Session State Variables:
        - st.session_state.session
        - st.session_state.emphasis
        - st.session_state.rec_id

    """

    # If the conversation is not from history, remove the rec_id from the session state
    if not historical:
        if "rec_id" in st.session_state:
            st.session_state.pop("rec_id")

    # Toggle emphasis in the history menu
    history_menu.toggle_emphasis(len(st.session_state.emphasis), no)

    # Start new session
    return new_session(run_id, user_id, language, historical)


# Function that creates a translator object for given language, based on predefined locales
def set_language(language: str) -> None:
    """
    Sets the language for the session.
    Creates the translator object for the given language and stores it in the session state.
    Library gettext is used for language translation.

    Args:
        language (str): The language code to set. 'sk' for Slovak, 'en' for English.

    Returns:
        None

    Influenced Session State Variables:
        - st.session_state.translator
        - st.session_state.session_lang

    Raises:
        FileNotFoundError: If the language translation file is not found.

    """

    try:
        # Load translation file for the given language
        lang_translations = gettext.translation(
            "base", localedir="locales", languages=[language]
        )
        lang_translations.install()

        # Create a translator object for the given language
        st.session_state.translator = lang_translations.gettext
        # Save the session language in the session state
        st.session_state.session_lang = language

    except FileNotFoundError as e:
        print(f"FAILED TO SET LOCALES: {e}")


def verify_authentication_flags() -> None:
    """
    This function verifies whether user has all required flags.

    Required flags are initialized in the session state.
    If the user does not have all required flags, the function shows error message.

    Args:
        None

    Returns:
        None

    """
    # No flags are currently checked on FE
    pass


def finish_authentication(auth_server_response) -> None:
    """
    Function that finishes the authentication flow.

    It sets the authenticated flag to True if the authentication flow is completed successfully and reruns the app.
    If the authentication flow is not completed successfully, it raises an UnauthorizedAccess exception and logs out the user.

    Args:
        auth_server_response (OAuth2Component): Object that contains the response from the authentication server.

    Returns:
        None

    """
    # If authentication flow is completed, save token in session state
    if auth_server_response and "token" in auth_server_response:

        # Save token in session state
        st.session_state.token = auth_server_response.get("token")

        # Extract user metadata from token
        auth.get_user_metadata(auth_server_response)

        # Set authenticated flag to True
        st.session_state.authenticated = True
        st.rerun()

    else:
        # If authentication flow is not completed successfuly, set authenticated flag to False
        st.session_state.authenticated = False


# FUTURE USE
def get_remote_ip() -> str:
    """
    Retrieve the remote IP address of the client.

    This function attempts to get the remote IP address of the client
    by accessing the session context and retrieving the client information.
    If the context or session information is not available, or if an 
    exception occurs, the function returns None.

    Returns:
        str: The remote IP address of the client, or None if it cannot be determined.
    """
    try:
        ctx = get_script_run_ctx()
        if ctx is None:
            return None

        session_info = runtime.get_instance().get_client(ctx.session_id)
        if session_info is None:
            return None
    except Exception as e:
        return None

    return session_info.request.remote_ip


def send_email_to_pgo(mail_body: str) -> None:
    """
    Send an email to the PGO with the provided mail body.

    Args:
        mail_body (str): The body of the email to be sent.

    Returns:
        None
    """
    # TO DO: implement email sending
    pass


class ContextFilter(logging.Filter):
    def filter(self, record):
        record.user_ip = get_remote_ip()
        return super().filter(record)


def regenerate_answer():
    # TO DO: implement answer regeneration
    pass
