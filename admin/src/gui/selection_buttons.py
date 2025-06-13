import streamlit as st

import src.utils.rag_endpoints as endpoints
from common.logging.st_logger import st_logger

from asyncio import run
from src.utils.helpers import get_rec_id, get_rec_descriptor
from src.utils.mongodb_adapter import delete_record, update_record_element, load_record, create_dataset_from_mongodb


def delete_btn(collection: str, df: object, selected_rows: list) -> None:
    """
    Delete records from MongoDB based on selected rows in DataFrame.
    Common steps for all collections.

    Args:
        collection (str): Name of collection in MongoDB
        df (object): pandas DataFrame object with records
        selected_rows (list): List of selected rows in DataFrame

    Returns:
        None
    """
    for selected_row_index in selected_rows:
        rec_id = get_rec_id(df, selected_row_index)
        rec_descriptor = get_rec_descriptor(collection, df, selected_row_index)
        st_logger.debug(f"Started deleting '{rec_descriptor}' with ID: {rec_id}")
        try:
            delete_one_record(collection, rec_id, rec_descriptor)
            st_logger.info(f"Deleted '{rec_descriptor}' with ID: {rec_id}")
        except Exception as e:
            st_logger.error(f"Error during deleting of item ID: {rec_id} {rec_descriptor}")  
            st.toast(st.session_state.translator(f"⚠️Error during deleting of: {rec_descriptor}"))
            
    st.session_state['dataset_' + collection] = create_dataset_from_mongodb(collection)
    st.toast(st.session_state.translator("Delete process finished ✔"))


def delete_one_record(collection: str, rec_id: str, rec_descriptor: str) -> None:
    """
    Delete one record from MongoDB based on selected row in DataFrame.
    Specific logic for each collection.

    Args:
        collection (str): Name of collection in MongoDB
        rec_id (str): ID of record in MongoDB
        rec_descriptor (str): Descriptor of record (filename, description, URL, etc.)

    Returns:
        None
    """
    match collection:
        case 'knowledge':
            # If the document is ingested, unlearn it and delete from Mongo
            record = load_record(rec_id, "knowledge")
            if record['header']['ingested']:
                response = run(endpoints.delete_delete_data(file_name=rec_descriptor))
                if endpoints.is_api_call_successful(response):
                    st_logger.info(response.text)
                    update_record_element(rec_id, 'ingested', False, "knowledge")
                    delete_record(rec_id, "knowledge")
                else:
                    st_logger.error(f"API error: {response.text}")
                    raise Exception(f"API error: {response.text}")
            else:
                # Remove the document from Mongo if it is not ingested
                delete_record(rec_id, "knowledge")

        case 'history':
            delete_record(rec_id, "history")

        case 'webscraper':
            # Delete page from Chroma
            response = run(endpoints.delete_delete_one_chroma_record(collection_name='webscraper', filter={"url" : rec_descriptor}))
            if endpoints.is_api_call_successful(response):
                # Delete page from Mongo
                response = run(endpoints.delete_delete_one_mongo_record(collection_name='webscraper', _id=rec_id))
                if endpoints.is_api_call_successful(response):
                    st_logger.debug(response.text)
                else:
                    st_logger.error(f"API error during deleting of '{rec_descriptor}' from Mongo: {response.text}")
                    raise Exception(f"API error Mongo: {response.text}")
            else:
                st_logger.error(f"API error during deleting of '{rec_descriptor}' from Chroma: {response.text}")
                raise Exception(f"API error Chroma: {response.text}")


def unlearn_btn(collection: str, df: object, selected_rows: list) -> None:
    """
    Unlearn records from MongoDB based on selected rows in DataFrame.
    Unearning means removing record from Chroma via API.
    Common steps for all collections.

    Args:
        collection (str): Name of collection in MongoDB
        df (object): pandas DataFrame object with records
        selected_rows (list): List of selected rows in DataFrame

    Returns:
        None
    """
    for selected_row_index in selected_rows:
        rec_id = get_rec_id(df, selected_row_index)
        rec_descriptor = get_rec_descriptor(collection, df, selected_row_index)
        st_logger.debug(f"Started unlearning '{rec_descriptor}' with ID: {rec_id}")
        try:
            unlearn_one_record(collection, rec_id, rec_descriptor)
            st_logger.info(f"Unlearned '{rec_descriptor}' with ID: {rec_id}")
        except Exception as e:
            st_logger.error(f"Error during unlearning of item ID: {rec_id} {rec_descriptor}")  
            st.toast(st.session_state.translator(f"⚠️Error during unlearning of: {rec_descriptor}"))
            
    st.session_state['dataset_' + collection] = create_dataset_from_mongodb(collection)
    st.toast(st.session_state.translator("Unlearn process finished ✔"))


def unlearn_one_record(collection: str, rec_id: str, rec_descriptor: str) -> None:
    """
    Unlearn one record from MongoDB based on selected row in DataFrame.
    Specific logic for each collection.

    Args:
        collection (str): Name of collection in MongoDB
        rec_id (str): ID of record in MongoDB
        rec_descriptor (str): Descriptor of record (filename, description, URL, etc.)

    Returns:
        None
    """
    match collection:
        case 'knowledge':
            record = load_record(rec_id, "knowledge")
            # If the document is ingested, unlearn it
            if record['header']['ingested']:
                response = run(endpoints.delete_delete_data(file_name=rec_descriptor))
                if endpoints.is_api_call_successful(response):
                    update_record_element(rec_id, 'ingested', False, "knowledge")
                    st_logger.debug(response.text)
                else:
                    st_logger.error(f"API error: {response.text}")
                    raise Exception(f"API error: {response.text}")

        case 'history':
            pass

        case 'webscraper':
            pass


def learn_btn(collection: str, df: object, selected_rows: list) -> None:
    """
    Learn records from MongoDB based on selected rows in DataFrame.
    Learning means ingesting record to Chroma via API.
    Common steps for all collections.

    Args:
        collection (str): Name of collection in MongoDB
        df (object): pandas DataFrame object with records
        selected_rows (list): List of selected rows in DataFrame

    Returns:
        None
    """
    for selected_row_index in selected_rows:
        rec_id = get_rec_id(df, selected_row_index)
        rec_descriptor = get_rec_descriptor(collection, df, selected_row_index)
        st_logger.debug(f"Started learning '{rec_descriptor}' with ID: {rec_id}")
        try:
            learn_one_record(collection, rec_id, rec_descriptor)
            st_logger.info(f"Learned '{rec_descriptor}' with ID: {rec_id}")
        except Exception as e:
            st_logger.error(f"Error during learning of item ID: {rec_id} {rec_descriptor}")
            st.toast(st.session_state.translator(f"⚠️Error during learning of: {rec_descriptor}"))
            
    st.session_state['dataset_' + collection] = create_dataset_from_mongodb(collection)
    st.toast(st.session_state.translator("Learn process finished ✔"))


def learn_one_record(collection: str, rec_id: str, rec_descriptor: str) -> None:
    """
    Learn one record from MongoDB based on selected row in DataFrame.
    Specific logic for each collection.

    Args:
        collection (str): Name of collection in MongoDB
        rec_id (str): ID of record in MongoDB
        rec_descriptor (str): Descriptor of record (filename, description, URL, etc.)

    Returns:
        None
    """
    match collection:
        case 'knowledge':
            record = load_record(rec_id, "knowledge")
            if not record['header']['ingested']:
                file = endpoints.convert_file_to_UploadFile(record['content'], record['header']['file_name'], record['header']['type'])
                response = run(endpoints.post_ingest_file(file))
                if endpoints.is_api_call_successful(response):
                    update_record_element(rec_id, 'ingested', True, "knowledge")
                    st_logger.debug(response.text)
                else:
                    st_logger.error(f"API error: {response.text}")
                    raise Exception(f"API error: {response.text}")

        case 'history':
            # previous conversation history is not ingested
            pass
            # record = load_record(rec_id, "history")
            # if not record['header']['ingested']:
            #     response = run(endpoints.post_ingest_text(str(record['conversation_content'])))
            #     if endpoints.is_api_call_successful(response):
            #         update_record_element(rec_id, 'ingested', True, "history")
            #         st_logger.debug(response.text)
            #     else:
            #         st_logger.error("API error: " + response.text)
            #         raise Exception(f"API error: {response.text}")

        case 'webscraper':
            pass
        