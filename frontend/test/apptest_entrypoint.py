import streamlit as st

from src.session import control


"""

An entrypoint for GUI tests which utilize streamlit.testing.v1 framework. 

"""


def setup_test_environment():

    st.session_state.authenticated = True
    st.session_state.user_id = "test@user.sk"
    st.session_state.user_name = "Test User"
    st.session_state.session_lang = "sk"

    control.set_language(st.session_state.session_lang)

    return True


def start_app():

    # st.set_page_config is not yet supported by streamlit.testing.v1 framework

    # st.set_page_config(
    #     page_title="FEI STU Chat",
    #     page_icon="💬",  
    #     layout="centered",    
    #     initial_sidebar_state="auto"  
    # )

    #Authentication is disabled for gui tests
    #auth.authenticate_user()

    #Setup test environment for gui testing
    if "configured" not in st.session_state:
        st.session_state.configured = setup_test_environment()
    

    if st.session_state.authenticated:

        #If any session is not initialized, initialize new session
        if "session" not in st.session_state:
            control.new_session(0,st.session_state.user_id,st.session_state.session_lang,False)

        #Start chat feature in current session
        st.session_state.session.chat()


#Main function call for chat_app
start_app()
