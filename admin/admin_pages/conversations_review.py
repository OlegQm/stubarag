import streamlit as st

from src.utils.mongodb_adapter import create_conversations_buffer
from src.session.conversations_evaluation import review_flow

def conversation_review() -> None:
    """
    Function that allows the admin user to review the conversations 
    that were held with the chatbot. The admin user can go through 
    the conversations one by one. Session state variables are declared.

    Args:
        None

    Returns:
        None

    """

    #Initialize 'conversation_index' variable, which is a session variable
    if 'review_conversations_buffer' not in st.session_state:
        st.session_state.review_conversations_buffer = create_conversations_buffer()

    #Initialize 'conversation_index' variable, which is a session variable
    if 'review_conversation_index' not in st.session_state:
        st.session_state.review_conversation_index = 0

    try:
        review_flow()
    except Exception as e:
        print(e)
        st.error(st.session_state.translator("⚠️Something went wrong, try again later⚠️"))
    

conversation_review()