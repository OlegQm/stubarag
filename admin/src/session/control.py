import streamlit as st
import gettext

import common.session.authentication as auth

from common.session.exceptions import UnauthorizedAccess
from src.utils.mongodb_adapter import create_dataset_from_mongodb


#Function that creates a translator object for given language, based on predefined locales
def set_language(language):

    try:
        lang_translations = gettext.translation('base', localedir='locales', languages=[language])
        lang_translations.install()
		
        st.session_state.translator = lang_translations.gettext
        st.session_state.session_lang = language

        # TODO - hotfix for promo, issue for complex fix created
        # Create datasets for knowledge and history when language is changed
        st.session_state.dataset_knowledge = create_dataset_from_mongodb("knowledge")
        st.session_state.dataset_history = create_dataset_from_mongodb("history")
        st.session_state.dataset_webscraper = create_dataset_from_mongodb("webscraper")
    
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

    if "unauthorized_flag" not in st.session_state:
        st.session_state.unauthorized_flag = False

    if st.session_state.unauthorized_flag:
        st.error(st.session_state.translator("ACCESS REJECTED: Only members of _admin_ group can access admin interface !"))


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

    try:
        if auth_server_response and 'token' in auth_server_response:
            # If authentication successful, save token in session state
            st.session_state.token = auth_server_response.get('token')

            auth.get_user_metadata(auth_server_response)
            auth.get_user_permissions(auth_server_response)

            if "admin-access" in st.session_state.user_permissions:
                st.session_state.authenticated = True
                st.session_state.unauthorized_flag = False
                st.rerun()
            else:
                raise UnauthorizedAccess()
        
    # Handle situation when unauthorized user try to log in
    except UnauthorizedAccess:
        st.session_state.unauthorized_flag = True
        auth.logout()
        st.rerun()
        
    else:
        st.session_state.authenticated = False