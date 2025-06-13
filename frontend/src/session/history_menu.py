import streamlit as st
from bson import ObjectId
from src.session import control, handlers, history

"""

A module for handling the conversation history menu located in sidebar.

"""


# New session for historical conversation is initiated within this function
def load_conversation(rec_id: ObjectId, user_id: str, no: int) -> None:
    """
    Callback function when historical conversation button is pressed.

    New session for conversation from history is initiated within this function.

    Args:
        rec_id (ObjectId): The ID of the conversation to load.
        user_id (str): The ID of the user.
        no (int): The order of conversation in history menu.

    Returns:
        None

    Influenced Session State Variables:
        - st.session_state.rec_id
        - st.session_state.run_id
        - st.session_state.session_lang
        - st.session_state.messages
        - st.session_state.memory

    """

    # Set the session conversation ID to the ID of the historical conversation
    st.session_state.rec_id = rec_id

    # Initiate a new session based on the historical conversation
    control.new_conversation(
        st.session_state.run_id + 1,
        user_id,
        st.session_state.session_lang,
        no=no,
        historical=True,
    )

    # Load the conversation content from conversation history
    st.session_state.messages = history.get_conversation_content(rec_id)


# Function that emphasise current chosen historical conversation in conversation menu
def toggle_emphasis(num: int, no: int = 0) -> None:
    """
    Toggles the emphasis of a list of elements in the session state.

    Emphasises the element at index 'no' as secondary Streamlit emphasis.

    Args:
        - num (int): The number of displayed conversations.
        - no (int, optional): The index of the element to be set as secondary emphasis. Defaults to 0.

    Returns:
        None

    Influenced Session State Variables:
        - st.session_state.emphasis

    """

    # Initialize the emphasis list to the default state
    st.session_state.emphasis = ["primary" for i in range(0, num)]

    # Emphasise the element at index 'no' as secondary emphasis
    st.session_state.emphasis[no] = "secondary"


# Function that handles behavior of top button in conversation history menu
def top_button(num: int, user_id: str) -> None:
    """
    Function to handle the top button in the history menu.

    When pressed, new conversation is initiated.

    Args:
        - num (int): The number of displayed conversations.
        - user_id (str): The ID of the user.

    Returns:
        None

    """

    # Initiate a new session for a new conversation
    control.new_conversation(
        st.session_state.run_id + 1, user_id, st.session_state.session_lang, False
    )

    # Toggle the emphasis of the conversation menu to the top conversation
    toggle_emphasis(num)


# Function that displays menu of historical conversations for 'user_id' user
def display(user_id: str) -> None:
    """
    Display the chat history menu for a given user in chat app sidebar.

    Args:
        - user_id (str): The ID of the user.

    Returns:
        - None

    Influenced Session State Variables:
        - st.session_state.conversations_id
        - st.session_state.emphasis
        - st.session_state.is_new
        - st.session_state.rec_id

    Raises:
        - IndexError: Error occured while loading historical conversations.

    """

    # Load the historical conversations for the user
    st.session_state.conversations_id = history.get_user_history(user_id)

    # Toggle the emphasis of the conversation menu to the default state
    if "emphasis" not in st.session_state:
        toggle_emphasis(len(st.session_state.conversations_id) + 1, 0)

    # Set the new conversation flag to False if conversation has been saved to the DB
    if "rec_id" in st.session_state:
        st.session_state.is_new = False

    # If the new chat is initiated, add it to the history menu
    if st.session_state.is_new is True:
        st.session_state.emphasis.append("primary")
        st.button(
            st.session_state.translator("Current chat"),
            type=st.session_state.emphasis[0],
            use_container_width=True,
            key="new_conversation",
            on_click=top_button,
            args=(
                len(st.session_state.conversations_id) + 1,
                user_id,
            ),
        )

    try:

        # If there are any historical conversations, display them in the history menu
        if (len(st.session_state.conversations_id)) >= 1:

            # Display a button for each historical conversation
            for i in range(0, len(st.session_state.conversations_id)):

                st.button(
                    history.get_title(st.session_state.conversations_id[i]),
                    type=st.session_state.emphasis[
                        ((i + 1) if st.session_state.is_new is True else i)
                    ],
                    use_container_width=True,
                    key=f"{st.session_state.conversations_id[i]}",
                    on_click=load_conversation,
                    args=(
                        st.session_state.conversations_id[i],
                        user_id,
                        ((i + 1) if st.session_state.is_new is True else i),
                    ),
                )

    except IndexError:
        print(
            f"[{handlers.timestamp()} : {__name__} - {display.__name__}] Error occured while loading historical conversations"
        )
