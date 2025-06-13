import streamlit as st

from src.gui.grid import print_dataframe
from src.gui.details_page_webscraper import details_page_header, details_page_body
from src.gui.upload_widgets import webscraper_form_widget, webscraper_csv_form_widget
from common.logging.st_logger import st_logger


# Initialize st.session state for Details Page
if "display_details_page_webscraper" not in st.session_state:
    st.session_state.display_details_page_webscraper = False

# Calls for default database interface page
def db_interface() -> None:
    """
    Entry point for the webscraper page. It contains the title, the form widget for the webscraper
    and table with scraped pages.

    Args:
        None
    Returns:
        None
    """
    st.title("🌐 Webscraper")
    if st.toggle(st.session_state.translator("Bulk insert")):
        webscraper_csv_form_widget()
    else:
        webscraper_form_widget()
    
    print_dataframe("webscraper")


# Calls for details page
def details_page() -> None:
    """
    Entry point for the details page. It contains the header and body of the details page.
    Single selected record is displayed in the body.

    Args:
        None
    Returns:
        None
    """
    details_page_header()
    details_page_body()
    

#Datails page or Database interface is run on this page based on flag
try:
    if st.session_state.display_details_page_webscraper:
        details_page()
    else:
        db_interface()
except Exception as e:
    st_logger.error(e)
    st.error(st.session_state.translator("⚠️Something went wrong, try again later⚠️"))
