import asyncio
import base64
import json
import os
import httpx
import streamlit as st

from common.session.decorators import http_timer

from httpx_oauth.oauth2 import OAuth2Token, RefreshTokenError
from streamlit_oauth import OAuth2Component

from src.gui import auth_page
from src.session.control import verify_authentication_flags, finish_authentication, set_language



def load_keycloak_vars() -> None:
    """
    Loads Keycloak authentication variables from environment variables and stores them in the session state.

    This function sets the following Keycloak variables in the session state:
    - authorize_url: The URL used for authorization.
    - token_url: The URL used for token retrieval.
    - refresh_token_url: The URL used for refreshing tokens.
    - logout_url: The URL used for logging out.
    - client_id: The client ID for authentication.
    - client_secret: The client secret for authentication.
    - redirect_uri: The redirect URI after authentication.
    - scope: The scope of the authentication.

    Note: The environment variables used to set these values should be defined before calling this function.

    Args:
        None

    Returns:
        None

    Influenced Session State Variables:
        - st.session_state.keycloak_vars

    """
    # Set environment variables
    st.session_state.keycloak_vars = {
        "authorize_url": os.getenv("AUTHORIZE_URL"),
        "token_url": os.getenv("TOKEN_URL"),
        "refresh_token_url": os.getenv("REFRESH_TOKEN_URL"),
        "logout_url": os.getenv("LOGOUT_URL"),
        "client_id": os.getenv("CLIENT_ID"),
        "client_secret": os.getenv("CLIENT_SECRET"),
        "redirect_uri": os.getenv("REDIRECT_URI"),
        "scope": os.getenv("SCOPE"),
    }


# Function that extract user metadata from OpenID section of JWT token
def get_user_metadata(jwt_token: dict) -> None:
    """
    Decodes provided JWT token and extracts user metadata.

    Args:
        jwt_token (dict): The JWT token containing user information.

    Returns:
        None

    Influenced Session State Variables:
        - st.session_state.user_name
        - st.session_state.user_id

    """

    # Extract the id_token from the JWT token
    id_token = jwt_token["token"]["id_token"]

    # Extract the body (payload) from the id_token
    payload = id_token.split(".")[1]
    # add padding to the payload if needed
    payload += "=" * (-len(payload) % 4)
    payload = json.loads(base64.b64decode(payload))

    # Extract the user metadata from the payload
    st.session_state.user_name = payload["name"]
    st.session_state.user_id = payload["preferred_username"]


#Function that extract user permissions(roles) from access section of JWT token
def get_user_permissions(jwt_token):
    """
    Decodes provided JWT token and extracts user permissions(roles).

    Args:
        jwt_token (dict): The JWT token containing user information.

    Returns:
        None

    Influenced Session State Variables:
        - st.session_state.user_permissions
    """

    access_token = jwt_token["token"]["access_token"]

    payload = access_token.split(".")[1]
    # add padding to the payload if needed
    payload += "=" * (-len(payload) % 4)
    payload = json.loads(base64.b64decode(payload))

    st.session_state.user_permissions = payload["resource_access"]["admin_client"]["roles"]


# Function that logout current user from running session
def logout() -> None:
    """
    Logs out the user by setting the 'authenticated' flag in the session state to False.

    It also deletes the 'token' and 'session' variables from the session state.
    Keycloak server is informed about the logout by calling the asynchronous function 'handle_keycloak_logout'.

    Args:
        None

    Returns:
        None

    Influenced Session State Variables:
        - st.session_state.authenticated
        - st.session_state.token
        - st.session_state.session

    """

    # Set authenticated flag to False
    st.session_state.authenticated = False

    # Inform keycloak server about the logout
    # Asynchronous function is used to handle the logout communication
    asyncio.run(handle_keycloak_logout())

    # Delete token and session from session state
    del st.session_state.token
    # diff in /admin - no st.session_state.session
    if "session" in st.session_state:
        del st.session_state.session
    

# Asynchronous function that handles logout communication with keycloak server
@http_timer
async def handle_keycloak_logout() -> bool:
    """
    Informs Keycloak server that user logged out.

    Keycloak invalidates the refresh token and the user is logged out on Keycloak side.

    Args:
        None

    Returns:
        bool: True if the logout was successful, False otherwise.

    """

    # Prepare the payload with the required parameters
    payload = {
        "client_id": st.session_state.keycloak_vars["client_id"],
        "client_secret": st.session_state.keycloak_vars["client_secret"],
        "refresh_token": st.session_state.token["refresh_token"],
    }

    # Send the POST request to the Keycloak server
    async with httpx.AsyncClient() as client:
        response = await client.post(
            st.session_state.keycloak_vars["logout_url"], data=payload
        )

        # Check the response
        if response.status_code == 204:
            return True
        else:
            print(f"Failed to logout. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False


def enable_guest_mode() -> None:
    """
    Enables the guest mode for the chat app session.

    This function sets the session state variables to simulate a guest user.
    It sets the `authenticated` flag to True, `user_id` to "guest@user.sk",
    and `user_name` to "Guest". If the `session_lang` variable is not already
    set in the session state, it sets it to "en" and calls the `set_language`
    function with the `session_lang` value.

    Args:
        None

    Returns:
        None

    Influenced Session State Variables:
        - st.session_state.authenticated
        - st.session_state.user_id
        - st.session_state.user_name
        - st.session_state.session_lang
        - st.session_state.translator

    """

    # Set the session state variables to simulate a guest user
    st.session_state.authenticated = True
    st.session_state.user_id = "guest@user.sk"
    st.session_state.user_name = "Guest"

    # Set the language to English if not already set
    if "session_lang" not in st.session_state:
        st.session_state.session_lang = "en"
        set_language(st.session_state.session_lang)


# Function that uses OAuth 2.0 protocol to authenticate user
def authenticate_user() -> None:
    """
    Authenticates the user using OAuth2 protocol.

    Internal Keycloak server is used for authentication.

    Args:
        None

    Returns:
        None

    Influenced Session State Variables:
        - st.session_state.oauth2
        - st.session_state.token
        - st.session_state.authenticated
        - st.session_state.user_name
        - st.session_state.user_id

    Raises:
        RefreshTokenError: If the refresh token is expired.

    Notes:
        This function checks if the necessary Keycloak variables are present in the session state. If not, it loads them.
        Then, it creates an OAuth2Component instance using the Keycloak variables.
        If the token is not present in the session state, it displays an authorization button for the user to log in.
        If the authentication is successful, the token is saved in the session state and the user's metadata is retrieved.
        If the access token is present but expired or invalid, it attempts to refresh the token.
        If the token refresh fails, the user is logged out and an error message is displayed.

    """

    # Load Keycloak variables
    if "keycloak_vars" not in st.session_state:
        load_keycloak_vars()
    # Create OAuth2Component instance
    if "oauth2" not in st.session_state:
        st.session_state.oauth2 = OAuth2Component(
            st.session_state.keycloak_vars["client_id"],
            st.session_state.keycloak_vars["client_secret"],
            st.session_state.keycloak_vars["authorize_url"],
            st.session_state.keycloak_vars["token_url"],
            st.session_state.keycloak_vars["refresh_token_url"],
        )

    # Check if token exists in session state
    if "token" not in st.session_state:
        # Set language to default (Slovak) if not set
        if "session_lang" not in st.session_state:
            set_language("sk")
        # Verify authentication flags
        verify_authentication_flags()
        # Display authentication page
        auth_page.create()
        spacer1, col, spacer2 = st.columns([0.7, 1, 0.7], vertical_alignment="center")

        with col:
            # If token doesnt exist in session state, show authorize button
            auth_server_response = st.session_state.oauth2.authorize_button(
                st.session_state.translator("Log in"),
                st.session_state.keycloak_vars["redirect_uri"],
                st.session_state.keycloak_vars["scope"],
                use_container_width=True,
                width=500,
                height=500,
                auto_click=False,
            )
        finish_authentication(auth_server_response)

    else:
        # If access token is present in session state, check if it is valid
        # If token expired or if it is invalid, refresh token
        try:
            st.session_state.token = st.session_state.oauth2.refresh_token(
                st.session_state.token
            )
        # If refresh token is too expired, inform user
        except RefreshTokenError:
            st.session_state.authenticated = False
            del st.session_state.token
            del st.session_state.session
            st.error(
                st.session_state.translator(
                    "You have been logged out due to inactivity"
                )
            )
        # If token refresh fail, inform user
        if "token" not in st.session_state or not isinstance(
            st.session_state.token, OAuth2Token
        ):
            st.session_state.authenticated = False
            st.error(st.session_state.translator("Something went wrong..."))
            