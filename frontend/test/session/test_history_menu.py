import pytest


"""

A set of unit tests for chat_app session package history_menu module.

"""


def test_load_conversation(get_user_history,mock_streamlit):

    conversations = get_user_history

    print(conversations)

    at = mock_streamlit

    run_id = at.session_state.run_id

    try:
        history_button = at.button(key=f"{conversations[0]['_id']}")

        history_button.click()
        
        at.run()

    except KeyError:
        assert False,"History conversation not accessible"

   
    assert run_id != at.session_state.run_id,"Failed to start new session"

    assert at.session_state.rec_id == conversations[0]['_id'],"Failed to set up rec_id as session state"

    assert at.session_state.messages == conversations[0]["conversation_content"], "Failed to set up historical messages as session state"


def test_toggle_emphasis(get_user_history,mock_streamlit):

    conversations = get_user_history
 
    at = mock_streamlit

    try:
       
        history_button = at.button(key=f"{conversations[0]['_id']}")

        history_button.click()
        at.run()
        
        assert at.session_state.emphasis[1] == "secondary","Failed to toggle emphasis"

        history_button = at.button(key=f"{conversations[1]['_id']}")

        history_button.click()
        
        at.run()

        assert at.session_state.emphasis[1] == "secondary","Failed to toggle emphasis"

        history_button = at.button(key=f"{conversations[2]['_id']}")

        history_button.click()
        
        at.run()

        assert at.session_state.emphasis[2] == "secondary","Failed to toggle emphasis"

    except KeyError:
        assert False,"History conversation not accessible"


def test_top_button(mock_streamlit):
    
    at = mock_streamlit

    run_id = at.session_state.run_id

    try:
        new_conversation__button = at.button(key="new_conversation")

        new_conversation__button.click()
        at.run() 

    except KeyError:
        assert False,"New conversation button not accessible"


    assert run_id != at.session_state.run_id,"Failed to start new session"

    assert at.session_state.emphasis[0] == "secondary","Failed to toggle emphasis"


def test_display(mock_streamlit):
    
    at = mock_streamlit

    assert len(at.session_state.emphasis) == 5, "Failed to initiate button emphasis"

    assert at.session_state.is_new == True,"Failed to initialize a new session"

    assert at.button.len == 8, "Failed to display history menu"
    # One "New Conversation" button, one "New chat" button, 
    # three conversation history buttons, two switch language buttons, one logout button
    