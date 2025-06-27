import json
import streamlit as st
from asyncio import run
from PIL import Image
from io import BytesIO

from common.logging.st_logger import st_logger
from src.session.endpoints import post_faq_random_questions
from src.gui import style

from common.session.db_connection import mongo_db


"""

A module for displaying the FAQ requestions for new LLM flow.

"""

def display_faq_tiles(number: int) -> None:
    """
    Function that retrieves and displays FAQ tiles in Streamlit application.

    Args:
        number (int): Number of FAQ tiles to be displayed
    Returns:
        None
    """
    # style.apply_faq_style()
    try:
        response = run(post_faq_random_questions("faq", number))
        faq_list = json.loads(response.text)
        questions_list = faq_list[0]["result"]
    except Exception as e:
        st_logger.error("Error during loading of faq list: " + str(e))
        return
    for question in questions_list:
        with st.expander(question["question"]):
            st.write(question["answer"])
    st.button(
        st.session_state.translator("Show all questions"),
        key="faq_all_questions",
        on_click=display_faq_list,
    )


@st.dialog("FAQ list", width="large")
def display_faq_list() -> None:
    """
    Function that retrieves and displays list of all FAQs.
    This function is called when the user clicks on the button to display all questions.
    Streamlit dialog is used to display the list, containing expandable rows.

    Args:
        None
    Returns:
        None
    """
    try:
        response = run(post_faq_random_questions("faq", 1000))
        faq_list = json.loads(response.text)
        questions_list = faq_list[0]["result"]
    except Exception as e:
        st_logger.error("Error during loading of faq list: " + str(e))
        st.title(st.session_state.translator("🔍The list is empty"))
        return
    for question in questions_list:
        with st.expander(question["question"]):
            st.write(question["answer"])


def display_news_tiles(number: int) -> None:
    """
    Function that retrieves and displays news tiles in Streamlit application.

    Args:
        number (int): Number of news tiles to be displayed
    Returns:
        None
    """
    mongo_db.set_collection("student_news")
    records = mongo_db.collection.find()
    try:
        record = records[0]
        st.write(record["content"])
    except Exception as e:
        st_logger.error("Error during loading of news list: " + str(e))
    try:
        image_bytes = record["image"]
        image = Image.open(BytesIO(image_bytes))
        st.image(image)
    except Exception as e:
        st_logger.error("Error during loading of image: " + str(e))
    st.button(
        st.session_state.translator("Show all news"),
        key="news_all_records",
        on_click=display_news_list,
    )


@st.dialog("FEI News list", width="large")
def display_news_list() -> None:
    """
    Function that retrieves and displays list of all FAQs.
    This function is called when the user clicks on the button to display all questions.
    Streamlit dialog is used to display the list, containing expandable rows.

    Args:
        None
    Returns:
        None
    """
    mongo_db.set_collection("student_news")
    records = mongo_db.collection.find()
    if records is None:
        st.title(st.session_state.translator("🔍The list is empty"))
        return   
    for record in records:
        try:
            with st.expander(record["title"], expanded=False):
                st.write(record["content"])
                try:
                    image_bytes = record["image"]
                    image = Image.open(BytesIO(image_bytes))
                    st.image(image, use_container_width=True)
                except Exception as e:
                    st_logger.error("Error during loading of image: " + str(e))
        except Exception as e:
            st_logger.error("Error during loading of news record: " + str(e))
