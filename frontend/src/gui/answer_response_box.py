import streamlit as st
from bson import ObjectId
from src.gui import style
from src.session import control, history

"""

A module for displaying the answer response options in the chat interface.

"""


# Function that displays answer response options and handle feedback associated tasks
def display(rec_id: ObjectId) -> None:
    """
    Displays a feedback interface for last LLM reply.

    Args:
        - rec_id (ObjectId): The record ID for which feedback is being provided.

    Returns:
        None

    Layout:
        - Feedback widget for providing feedback on the answer.
        - A button for regenerating the answer.
    """

    # Display feedback interface
    with st.container(border=False):
        spacer, feedback, regenerate = st.columns([15, 2, 1])
        # Display st.feedback widget for providing feedback on the answer
        with feedback:
            # Each feedback widget displayed needs unique key
            recorded_feedback = st.feedback(
                key="feedback_widget"+str(len(st.session_state.messages)),
                options="thumbs",
            )
            if recorded_feedback == 0:
                history.record_feedback("bad", rec_id)
            elif recorded_feedback == 1:
                history.record_feedback("good", rec_id)

        # Display button for regenerating the answer
        with regenerate:
            regenerate = st.button(
                "🔄",
                help=st.session_state.translator("Regenerate answer"),
                disabled=False,
                on_click=control.regenerate_answer,
            )
            style.change_button_size("🔄", 75)
