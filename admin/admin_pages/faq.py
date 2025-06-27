import streamlit as st

from src.gui.upload_widgets import faq_form_widget
from common.logging.st_logger import st_logger
from src.gui.faq_list import faq_list_display


# # Initialize st.session state for Details Page
# if "display_details_page_webscraper" not in st.session_state:
#     st.session_state.display_details_page_webscraper = False

# Calls for default database interface page
def db_interface() -> None:
    """
    Entry point for the faq page. It contains the title, the form widget for the faq imput
    and table with faq entries.

    Args:
        None
    Returns:
        None
    """
    st.title("❓ FAQ")
    faq_form_widget()
    faq_list_display()


# Calls for details page
# def details_page() -> None:
#     """
#     Entry point for the details page. It contains the header and body of the details page.
#     Single selected record is displayed in the body.

#     Args:
#         None
#     Returns:
#         None
#     """
#     details_page_header()
#     details_page_body()
    

#Datails page or Database interface is run on this page based on flag
try:
    # if st.session_state.display_details_page_webscraper:
    #     details_page()
    # else:
    #     db_interface()
    db_interface()
except Exception as e:
    st_logger.error(e)
    st.error(st.session_state.translator("⚠️Something went wrong, try again later⚠️"))
