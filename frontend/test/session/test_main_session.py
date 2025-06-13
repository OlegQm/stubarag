import pytest
import gettext

"""

A set of unit tests for chat_app session package main_session module.

"""

@pytest.mark.skip(reason="This test needs update because of connection_LLM.py changes")
#Test of Session object initialization
def test_Session_intitialization(mock_streamlit):
    
    at = mock_streamlit

    assert at.session_state.run_id == 0
    assert at.session_state.user_id == "test@user.sk" 
    assert at.session_state.historical == False

    from PIL.Image import Image
    assert isinstance(at.session_state.assistant_icon,Image)
    assert at.session_state.history_enabled == True or at.session_state.history_enabled == False
    assert len(at.session_state.openai_model) > 0
    assert at.session_state.messages == []

    from langchain.chains import ConversationChain
    assert isinstance(at.session_state.chain,ConversationChain)

    assert at.session_state.response_received == False
    assert at.session_state.is_new == True
    assert at.session_state.historical == False


#Test of Session class chat() method
def test_chat(mock_streamlit):
   
    at = mock_streamlit

    try:
        user_input = at.chat_input[0]

        assert user_input is not None, "Chat_input field is not present in Streamlit app"

    except IndexError:
        assert False, "Chat_input field is not present in Streamlit app"

    try:
        sidebar = at.sidebar[0]

        assert sidebar is not None, "Sidebar is not present in Streamlit app"

    except IndexError:
        assert False, "Sidebar is not present in Streamlit app"


    try:
        main_title = at.markdown[1]

        assert main_title is not None,"Main title not present in Streamlit app"

    except IndexError:
        assert False, "Main title not present in Streamlit app"


    user_input.set_value("What is the meaning of life ?")

    at.run()

    try:
        user_prompt = at.chat_message[0]

        assert user_prompt is not None,"Failed to display user prompt"

    except IndexError:
        assert False,"Failed to display user prompt"

    at.run()

    try:
        llm_response = at.chat_message[1]

        assert llm_response is not None,"Failed to display LLM response"

    except IndexError:
        assert False,"Failed to display LLM response"