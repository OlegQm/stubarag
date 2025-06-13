import streamlit as st

from src.utils.helpers import get_rec_id
from src.utils.mongodb_adapter import load_record
from common.logging.st_logger import st_logger

# Displays title and navigation elements
def details_page_header():
    st.title(st.session_state.translator("Conversation details"))
    if st.button(st.session_state.translator("Back")):
        st.session_state.details_row_index_history = None
        st.session_state.display_details_page_history = False
        st.rerun()


# Displays actual details of given conversation
def details_page_body():
    df = st.session_state.dataset_history
    selected_row_index = st.session_state.details_row_index_history
    record = load_record(get_rec_id(df, selected_row_index), "history")
    conversation_content = record['conversation_content']

    st.write(record['header']['title'])
    display_conversation_content(conversation_content)


def display_conversation_content(conversation_content: list) -> None:    
    """
    Method that parse conversation and prints it on screen as chatbot conversation.

    Args:
        - conversation_content (list): List of dictionaries containing messages in the conversation

    Returns:
        None
    """
    if conversation_content is None:
        return
    try:
        for message in conversation_content:
            if message["role"] == "assistant":
                with st.chat_message(
                    message["role"], avatar=st.session_state.assistant_icon
                ):
                    st.markdown(message["content"])
            else:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
    except Exception as e:
        st_logger.error(e)
        st.error("Error during conversation content display")