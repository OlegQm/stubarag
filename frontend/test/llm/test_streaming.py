import pytest
import streamlit as st


"""

A set of unit tests for chat_app llm package streaming module.

"""

@pytest.mark.skip(reason="connection_LLM.py is deprecated and will be removed")
def test_StreamHandler_initialization():

    from src.llm.streaming import StreamHandler

    container = st.empty()

    sh = StreamHandler(container)

    assert sh.container == container, "Failed to set container for streaming"
    assert sh.text == '', "Failed to set initial text"
    assert sh.display_method == "markdown", "Failed to set display method"

@pytest.mark.skip(reason="connection_LLM.py is deprecated and will be removed")
def test_on_llm_new_token():

    from src.llm.streaming import StreamHandler

    container = st.empty()

    sh = StreamHandler(container)

    sh.on_llm_new_token("fei")

    assert sh.text == "fei","Failed to stream a token"
