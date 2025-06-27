import streamlit as st

from src.gui.grid import print_dataframe
from src.gui.upload_widgets import file_upload_widget
from src.gui.details_page_knowledge import details_page_header, details_page_body
from common.logging.st_logger import st_logger

# Initialize st.session state for Details Page
if "display_details_page_knowledge" not in st.session_state:
    st.session_state.display_details_page_knowledge = False

# Calls for default database interface page
def db_interface():
    st.title(st.session_state.translator("📚 Knowledge base"))
    
    file_upload_widget()
    print_dataframe("knowledge")


# Calls for details page
def details_page():
    details_page_header()
    details_page_body()


# Datails page or Database interface is run on this page based on flag
try:
    if st.session_state.display_details_page_knowledge:
        details_page()
    else:
        db_interface()
except Exception as e:
    st_logger.error(e)
    st.error(st.session_state.translator("⚠️Something went wrong, try again later⚠️"))
