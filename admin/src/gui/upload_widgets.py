import streamlit as st
from src.gui.style import apply_style_file_uploader
from common.session.exceptions import UnsupportedFile
from src.utils.mongodb_adapter import create_dataset_from_mongodb
from src.utils.upload import process_zip_and_upload, webscraper_form, webscraper_csv_form, faq_form
from src.utils.mongodb_adapter import upload_file


# Form widget that requires submit button
def file_upload_widget():
    with st.form(key="admin_uploader", clear_on_submit=True):
        uploaded_files = st.file_uploader(
            st.session_state.translator("Upload a file"),
            type=["pdf", "zip"],
            accept_multiple_files=True,
        )
        apply_style_file_uploader()
        submitted = st.form_submit_button(st.session_state.translator("UPLOAD FILE"))

        # If file was submited, custom handling function is called
        if submitted and len(uploaded_files):
            # Call for MongoDB communication function

            try:
                for file in uploaded_files:
                    if "zip" in file.type:
                        process_zip_and_upload(file)
                    elif (
                        file.type == "application/pdf"
                        or file.type == "application/json"
                    ):
                        upload_file(file, "knowledge")
                    else:
                        raise UnsupportedFile(
                            st.session_state.translator("Unsupported file type !")
                        )

            except UnsupportedFile as error:
                st.error(
                    st.session_state.translator("Error processing file ")
                    + f"'{file.name}': "
                    + f"{st.session_state.translator(error)}"
                )

            uploaded_files = []
            st.session_state.dataset_knowledge = create_dataset_from_mongodb("knowledge")


def webscraper_form_widget() -> None:
    """
    Function that creates a form widget for the admin user to input the URL and description of the website
    that they want to scrape. The form is submitted by the admin user.

    Args:
        None

    Returns:
        None
    """

    with st.form(key="admin_webscraper", clear_on_submit=True):
        st.write(st.session_state.translator("Enter information about webpage"))
        url_input = st.text_input(
            "URL"
        )
        description_input = st.text_input(
            st.session_state.translator("Description of the website")
        )
        submitted =  st.form_submit_button(st.session_state.translator("Submit"))

        if submitted:
            if not url_input:
                st.toast(st.session_state.translator("⚠️URL is empty!"))
                return
            if not description_input:
                st.toast(st.session_state.translator("⚠️Description is empty!"))
                return
            webscraper_form(url_input, description_input)
            st.session_state.dataset_webscraper = create_dataset_from_mongodb("webscraper")


def webscraper_csv_form_widget() -> None:
    """
    Function that creates a form widget for the admin user to input the URLs and descriptions of the websites
    that they want to scrape in file format (CSV). The form is submitted by the admin user.

    Args:
        None

    Returns:
        None
    """

    with st.form(key="admin_webscraper_csv", clear_on_submit=True):
        uploaded_file = st.file_uploader(
            st.session_state.translator("Upload a file in format:    | Description | URL |"),
            help="First column should be description and second column should be URL of website. Example: | Description | URL |",
            type=["csv"],
            accept_multiple_files=False,
        )
        apply_style_file_uploader(webscraper = True)
        submitted = st.form_submit_button(st.session_state.translator("START SCRAPING"))
        # If file was submited, custom handling function is called
        if submitted and uploaded_file:
            webscraper_csv_form(uploaded_file)
            uploaded_file = None
            st.session_state.dataset_webscraper = create_dataset_from_mongodb("webscraper")


def faq_form_widget() -> None:
    """
    Function that creates a form widget for the admin user to input the URL and description of the website
    that they want to scrape. The form is submitted by the admin user.

    Args:
        None

    Returns:
        None
    """
# TODO add url and doc (optional for endpoint)
    with st.form(key="admin_faq", clear_on_submit=True):
        st.write(st.session_state.translator("Enter question and answer pair"))
        url_input = st.text_input(
            st.session_state.translator("Question")
        )
        description_input = st.text_input(
            st.session_state.translator("Answer")
        )
        submitted = st.form_submit_button(st.session_state.translator("Submit"))

        if submitted:
            if not url_input:
                st.toast(st.session_state.translator("⚠️Question is empty!"))
                return
            if not description_input:
                st.toast(st.session_state.translator("⚠️Answer is empty!"))
                return
            faq_form(url_input, description_input)
