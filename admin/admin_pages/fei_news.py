import streamlit as st

from common.session.db_connection import mongo_db
from common.logging.st_logger import st_logger
from PIL import Image
import io


def display_fei_news():
    """
    Entry point for the FEI news page. Every record is in expander form with
    title, content and image. Each record has a delete button, which deletes the
    record from the MongoDB collection.

    Args:
        None
    Returns:
        None
    """
    st.title(st.session_state.translator("📰 FEI News"))
    mongo_db.set_collection("student_news")
    records = mongo_db.collection.find()
        
    for record in records:
        try:
            with st.expander(record["title"], expanded=False):
                st.write(record["content"])
                try:
                    image_bytes = record["image"]
                    image = Image.open(io.BytesIO(image_bytes))
                    st.image(image, use_container_width=True)
                except Exception as e:
                    st_logger.error("Error during loading of image: " + str(e))
                st.button(
                    st.session_state.translator("Delete"),
                    key=str('delete_news_' + str(record["message_id"])),
                    on_click=on_click_delete_news_record,
                    args=[record["_id"]]
                )
        except Exception as e:
            st_logger.error("Error during loading of record: " + str(e))
            st.error("Error during loading of record.")
            with st.expander("CORRUPTED RECORD⚠️", expanded=False):
                st.write(record)
                st.button(
                    st.session_state.translator("Delete"),
                    key=str('delete_news_' + str(record["message_id"])),
                    on_click=on_click_delete_news_record,
                    args=[record["_id"]]
                )


def on_click_delete_news_record(record_id):
    """
    Delete a record from the MongoDB collection.

    Args:
        record_id (str): The ID of the record to be deleted.
    Returns:
        None
    """        
    try:
        mongo_db.collection.delete_one({"_id": record_id})
        st.toast(st.session_state.translator("Delete process finished ✔"))
        st_logger.info(f"Deleted successfully news record: '{record_id}'")
    except Exception as e:
        st_logger.error("Error during deleting of news record: " + record_id)  
        st.toast(st.session_state.translator("⚠️Error during deleting of News record"))

# Main entry point for the FEI news page
try:
    display_fei_news()
except Exception as e:
    st_logger.error(e)
    st.error(st.session_state.translator("⚠️Something went wrong, try again later⚠️"))