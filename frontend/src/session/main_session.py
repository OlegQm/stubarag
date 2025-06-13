from common.llm_adapters.frontend_adapter import FrontendFlow
import streamlit as st
from src.gui import answer_response_box, sidebar, style, before_chat_interface
from common.llm import streamhandler

# Import custom app modules
from src.session import control, history
from PIL import Image


class Session:
    """
    Session class for managing a chat session in a Streamlit application.

    Attributes:
        run_id (str): Identifier for the session run.
        user_id (str): Identifier for the user.
        language (str): Language for the session.
        historical (bool): Flag indicating if the session is based on historical conversation.

    Methods:
        __init__(run_id, user_id, language, historical):
            Initializes the session with the given parameters and sets up the session state.
        chat():
            Manages the chat feature of the Streamlit session, including displaying messages,
            accepting user input, recording of the conversation and handling responses from
            the language model.

    """

    def __init__(
        self, run_id: str, user_id: str, language: str, historical: bool
    ) -> None:

        # Add session run identifier 'run_id' to session_state
        st.session_state.run_id = run_id
        # Initialize user_id for current session
        st.session_state.user_id = user_id
        # Set assistant icon for streamlit frontend
        st.session_state.assistant_icon = Image.open(".streamlit/icon.png")
        # Initialize 'conversation history enabled' flag
        st.session_state.history_enabled = True
        # Initialize chat history
        st.session_state.messages = []
        # Initialize 'response_received' as a session variable
        st.session_state.response_received = False
        # Set flag that marks whether user interacted with chat_app
        st.session_state.is_new = False if historical else True
        # Flag that marks whether conversation from history
        st.session_state.historical = historical
        # Current session language:
        st.session_state.session_lang = language
        # Initialize a phase counter for the session
        st.session_state.phase = (4 if historical else 0)
        # Initialize a handler of conversation flow
        st.session_state.flow_handler = FrontendFlow()
        # Set language for current session and create a translator function for that language
        control.set_language(language)
        # Initialize a flag that marks whether chat input from user is possible
        st.session_state.input_disabled = False


    # Method for chat feature of Streamlit session
    def chat(self) -> None:
        """
        Handles the main chat functionality of the application.

        This method performs the following tasks:
        1. Creates the main title for the app's main page.
        2. Creates a sidebar for the Streamlit app.
        3. Displays chat messages of the current conversation on app rerun.
        4. Accepts user input and adds it to the chat history.
        5. Sends the user query to the LLM and receives a response.
        6. Displays the assistant's response in the chat message container.
        7. Opens a stream for recording the conversation if it's a new conversation.
        8. Records the current user question and LLM reply to the history record in MongoDB.
        9. Appends the current user question and LLM reply to the LLM conversation buffer.
        10. Displays the answer response box if a response from the LLM is received.

        Args:
            None

        Returns:
            None

        """

        # Create a main title for app main page
        style.create_main_title("FEI STU Chat")

        # Create sidebar for Streamlit app
        sidebar.create(st.session_state.user_id)

        # Display FAQ tiles if this is the beginning phase (0) of the conversation
        if st.session_state.phase == 0:
            before_chat_container = st.empty()
            with before_chat_container:
                before_chat_tabs = st.tabs(["FAQ", "FEI News"])
                with before_chat_tabs[0]:
                    before_chat_interface.display_faq_tiles(3)
                with before_chat_tabs[1]:
                    before_chat_interface.display_news_tiles(3)

        # Display chat messages of current conversation on app rerun
        for message in st.session_state.messages:
            if message["role"] == "assistant":
                with st.chat_message(
                    message["role"], avatar=st.session_state.assistant_icon
                ):
                    st.markdown(message["content"])
            else:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
    
        # Accept user input
        if prompt := st.chat_input(
            st.session_state.translator("What is on your mind, ")
            + str(st.session_state.user_name),
            disabled=(st.session_state.input_disabled or st.session_state.historical),
            key="chat_input",
            on_submit= (lambda: setattr(st.session_state, 'input_disabled', True) if st.session_state.phase >= 200 else None)

        ):
            # Move to the next phase of the conversation
            if st.session_state.phase == 0:
                before_chat_container.empty()
            st.session_state.phase += 1

            # Add user message to chat history
            st.session_state.messages.append(
                {"role": "user", "content": prompt})
            st.session_state.feedback_submited = False
            # Display user message in chat message container
            with st.chat_message("user"):
                st.markdown(prompt)

            # Display assistant response in chat message container in form of a stream
            with st.chat_message("assistant", avatar=st.session_state.assistant_icon):

                # Create a stream handler for streaming of assistant response
                stream_handler = streamhandler.StreamHandler(
                    st.empty(), display_method="markdown"
                )

                # Send user query to LLM and receive response
                response = st.session_state.flow_handler.send_query(
                    st.session_state.messages,
                    st.session_state.phase,
                    stream_handler,
                    st.session_state.translator
                )

                # Append assistant response to chat history
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )
                # Set flag that response from LLM was received
                st.session_state.response_received = True

            # Open stream for recording of conversation if this is new conversation
            if (not st.session_state.historical) and ("rec_id" not in st.session_state):
                st.session_state.rec_id = history.open_history_stream(
                    st.session_state.user_id
                )

            # Append current user question and LLM reply to the history record in MongoDB history collection
            history.record_history(
                st.session_state.messages, st.session_state.rec_id)


        # Display answer response box if response from LLM received
        if st.session_state.response_received:
            answer_response_box.display(st.session_state.rec_id)


        if (st.session_state.phase >= 3 and not (st.session_state.input_disabled or st.session_state.historical)):
            with st.popover(st.session_state.translator("Contact PGO")):
                mail_body = st.text_input(
                    label=st.session_state.translator("Your message to PGO"),
                    value=st.session_state.translator("Dear PGO..."),
                )
                st.button(
                    st.session_state.translator("Send"),
                    key="send_email",
                    on_click=control.send_email_to_pgo,
                    args=[mail_body],
                )