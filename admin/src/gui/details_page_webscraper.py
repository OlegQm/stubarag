import streamlit as st

from src.utils.helpers import get_rec_id
from common.session.db_connection import mongo_db
from common.logging.st_logger import st_logger


# Displays title and navigation elements
def details_page_header() -> None:
    """
    Displays title and navigation elements

    Args:
        None
    
    Returns:
        None
    """
    st.title(st.session_state.translator("Webscraper page details"))
    if st.button(st.session_state.translator("Back")):
        st.session_state.details_row_index_webscraper = None
        st.session_state.display_details_page_webscraper = False
        st.rerun()


# Displays actual details of given conversation
def details_page_body() -> None:
    """
    Displays actual details of given conversation (webscraper record in JSON format)

    Args:
        None

    Returns:
        None 
    """
    df = st.session_state.dataset_webscraper
    selected_row_index = st.session_state.details_row_index_webscraper
    mongo_db.set_collection('webscraper')
    try:
        history_data = mongo_db.collection.find_one({"_id":get_rec_id(df, selected_row_index)})
        if history_data is None:
            raise Exception
    except Exception:
        st_logger.error(st.session_state.translator("Requested conversation does not exist: ")+f"{0}")
    st.write(history_data, width=500)
    