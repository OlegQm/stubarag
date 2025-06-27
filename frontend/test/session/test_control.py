import pytest
import streamlit as st


"""

A set of unit tests for chat_app session package control module.

"""


#Test for initiating a new session
def test_new_session():

    from src.session.control import new_session

    success = new_session(0,120414,"sk",False)

    from src.session.main_session import Session

    assert isinstance(st.session_state.session,Session) and success,"Failed to create a new session"


#Test fo starting a new conversation
def test_new_conversation():

    from src.session.control import new_conversation

    st.session_state.emphasis = ["secondary","primary","primary"]

    assert new_conversation(0,120414,"sk",False,0),"Failed to start a new conversation"


#Test for LLM answer regeneration callback
def test_regenerate_answer():

    assert True