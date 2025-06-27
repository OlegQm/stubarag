import streamlit as st
import zipfile
import magic
import pandas as pd

from asyncio import run

from src.utils.mongodb_adapter import upload_file
from common.session.exceptions import UnknownFileType, UnsupportedFile
import src.utils.rag_endpoints as endpoints
from common.logging.st_logger import st_logger


# A wrapper that wraps around zipfile.ZipExtFile class
# A wrapped file is compatible with existing file upload infrastructure
class UploadedFileWrapper:
    def __init__(self, zip_ext_file, file_name):
        self.zip_ext_file = zip_ext_file
        self._file_name = file_name
        self._file_data = zip_ext_file.read()
    
    def read(self):
        return self._file_data
    
    @property
    def size(self):
        return len(self._file_data)
    
    @property
    def name(self):
        return self._file_name
    
    @property
    def type(self):

        mime = magic.Magic(mime=True)

        mime_type = mime.from_buffer(self._file_data)

        if mime_type == "application/octet-stream":
            raise UnknownFileType(st.session_state.translator("Failed to recognize file type ! File formatting may be broken."))
        
        return mime_type 


# Function that extracts content of uploaded ZIP file and uploads it to MongoDB history collection
def process_zip_and_upload(zip_file):
    error_occured = False
    try:
        with zipfile.ZipFile(zip_file) as z:
            for file_name in z.namelist():
                if not file_name.endswith('/'):
                    with z.open(file_name) as extracted_file:
                        try:
                            wrapped_file = UploadedFileWrapper(extracted_file, file_name)
                            if wrapped_file.type is None:
                                continue
                            if wrapped_file.type == 'application/pdf' or wrapped_file.type == 'application/json':
                                upload_file(wrapped_file, "knowledge")
                            else:
                                raise UnsupportedFile(st.session_state.translator("Unsupported file type !"))
                        except (UnknownFileType, UnsupportedFile) as error:
                            st.error(st.session_state.translator("Error processing file ")+f"'{wrapped_file.name}': "+f"{st.session_state.translator(error)}")
                            error_occured = True
    except zipfile.BadZipFile as error:
        st.error(st.session_state.translator("Error processing ZIP file ")+f"'{zipfile.ZipFile(zip_file).filename}': "+f"{st.session_state.translator(error)}")
        error_occured = True

    if not error_occured:
        st.toast(st.session_state.translator("ZIP file uploaded successfully"))


def webscraper_form(url_input: str, description_input: str) -> None:
    """
    Function that handles the form submission for the webscraper

    Args:
        url_input (str): URL of the website to scrape from
        description_input (str): Description of the website

    Returns:
        None

    """
    owner = st.session_state.user_name
    # Call endpoint
    response = run(endpoints.post_webscraper(url_input, description_input, owner))
    # Check if the API call was successful
    if endpoints.is_api_call_successful(response):
        st.toast(st.session_state.translator("Webscraper process finished successfully"))
    else:
        st_logger.error("Webscraper process failed: " + response.text)
        st.toast(st.session_state.translator("⚠️Webscraper process failed"))


def webscraper_csv_form(uploaded_file: object) -> None:
    """
    Function that handles the form submission for the webscraper from file.
    It parses the file and processes the webpages.

    Args:
        upload_file (object): streamlit file object that contains the webpages to scrape

    Returns:
        None
    """
    reader = pd.read_csv(uploaded_file, header=None)
    owner = st.session_state.user_name
    for row in reader.iterrows():
        description = row[1][0]
        url = row[1][1]
        # Call endpoint
        response = run(endpoints.post_webscraper(url, description, owner))
        # Check if the API call was successful
        if endpoints.is_api_call_successful(response):
            st_logger.info("Page scraped successfully: " + url)
        else:
            st_logger.error("Webscraper process failed: " + response.text)
            st.toast(st.session_state.translator("⚠️Webscraper process failed"))
    st.toast(st.session_state.translator("Webscraper process finished successfully"))

def faq_form(question: str, answer: str) -> None:    # TODO add url and doc (optional for endpoint)
    """
    Function that handles the form submission for the FAQ

    Args:
        question (str): Frequently asked question (FAQ) by users
        answer (str): Answer to the question

    Returns:
        None

    """
    # Call endpoint
    response = run(endpoints.post_faq_load_records(question, answer))
    # Check if the API call was successful
    if endpoints.is_api_call_successful(response):
        st.toast(st.session_state.translator("Upload process finished successfully"))
    else:
        st_logger.error("Upload process failed: " + response.text)
        st.toast(st.session_state.translator("⚠️Upload process failed"))
