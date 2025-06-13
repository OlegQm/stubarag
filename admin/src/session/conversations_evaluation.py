import streamlit as st

from src.utils.mongodb_adapter import update_record_element
from src.gui.details_page_history import display_conversation_content
from common.logging.st_logger import st_logger

def review_flow():
    """
    Function that allows the admin user to review the conversations
    that were held with the chatbot. Actual interface and logic is
    implemented here.

    Args:
        None

    Returns:
        None

    """
    
    try:
        conversations_num = st.session_state.review_conversations_buffer.explain().get("executionStats", {}).get("nReturned")
    except Exception as e:
        st_logger.error(e)
        st.write(st.session_state.translator("No conversations for review"))
        return

    st.header(st.session_state.translator("Conversations review"))
    st.text(st.session_state.translator("Number of conversations to be reviewed: ") + str(conversations_num))
    if conversations_num == 0:
        st.header(st.session_state.translator("All conversations are already reviewed! 🎉🥳 Come back later."))
        return

    #Create two columns for button placement
    col1, col2 = st.columns([2.5,1.0])
    if st.session_state.review_conversation_index < 0:
        st.session_state.review_conversation_index = 0
    #Create 'Next conversation' and 'Previous conversation' buttons
    #Session state variable 'review_conversation_index' is updated when each button is pressed
    with col1:
        st.button(
            st.session_state.translator("Previous conversation"), 
            disabled=st.session_state.review_conversation_index <= 0,
            on_click=on_previous_click
        )  
    with col2:
        st.button(
            st.session_state.translator("Next conversation"), 
            disabled=st.session_state.review_conversation_index >= conversations_num - 1,
            on_click=on_next_click
        )

    try:
        conversation = st.session_state.review_conversations_buffer[st.session_state.review_conversation_index]['conversation_content']
    except Exception as e:
        st_logger.error(e)
        st.error(st.session_state.translator("No conversation content to display"))
        conversation = None
    try:
        conversation_review_value = st.session_state.review_conversations_buffer[st.session_state.review_conversation_index]['header']['review']
    except Exception as e:
        st_logger.error(e)
        conversation_review_value = None

    if conversation_review_value == 'good':
        st.header(st.session_state.translator("Konverzácia už bola ohodnotená ako DOBRÁ ✅!"))
    elif conversation_review_value == 'bad':
        st.header(st.session_state.translator("Konverzácia už bola ohodnotená ako ZLÁ ❌!"))
    #Display current conversation
    display_conversation_content(conversation)

    #Create three columns (one dummy column only as spacer)
    colX, col3, col4 = st.columns([0.4, 0.6, 1.0])

    #Place evaluation buttons in each column
    with col3:
        st.button(
            st.session_state.translator("❌ Bad conversation"),
            disabled=conversation_review_value == 'bad',
            on_click=on_bad_click,
            args=[conversations_num]
        )
    with col4:
        st.button(
            st.session_state.translator("✅ Good conversation"),
            disabled=conversation_review_value == 'good',
            on_click=on_good_click,
            args=[conversations_num]
        )


def on_next_click():
    """
    Function that updates the session state variable 'review_conversation_index'
    when the 'Next conversation' button is clicked.

    Args:
        None

    Returns:
        None

    """
    st.session_state.review_conversation_index += 1


def on_previous_click():
    """
    Function that updates the session state variable 'review_conversation_index'
    when the 'Previous conversation' button is clicked.

    Args:
        None

    Returns:
        None

    """
    st.session_state.review_conversation_index -= 1


def on_bad_click(conversations_num: int):
    """
    Function that updates the review value of the conversation to 'bad'
    when the 'Bad conversation' button is clicked.

    Args:
        conversations_num (int): Number of conversations in the buffer

    Returns:
        None

    """
    rec_id = st.session_state.review_conversations_buffer[st.session_state.review_conversation_index]['_id']
    update_record_element(
        rec_id,
        'review',
        'bad',
        'history',
    )
    update_record_element(
        rec_id,
        'reviewed_by',
        st.session_state.user_name,
        'history',
    )
    if st.session_state.review_conversation_index >= conversations_num - 1:
        st.session_state.review_conversation_index -= 1
    st_logger.info(f"Conversation {rec_id} review set to 'good'")


def on_good_click(conversations_num: int):
    """
    Function that updates the review value of the conversation to 'good'
    when the 'Good conversation' button is clicked.

    Args:
        conversations_num (int): Number of conversations in the buffer

    Returns:
        None

    """ 
    rec_id = st.session_state.review_conversations_buffer[st.session_state.review_conversation_index]['_id']
    update_record_element(
        rec_id,
        'review',
        'good',
        'history',
    )
    update_record_element(
        rec_id,
        'reviewed_by',
        st.session_state.user_name,
        'history',
    )
    if st.session_state.review_conversation_index >= conversations_num - 1:
        st.session_state.review_conversation_index -= 1
    st_logger.info(f"Conversation {rec_id} review set to 'good'")

