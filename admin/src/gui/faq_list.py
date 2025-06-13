import streamlit as st
import json

from asyncio import run

from common.logging.st_logger import st_logger
import src.utils.rag_endpoints as endpoints

def faq_list_display(num_of_rows: int = 1000) -> None:
    """
    Display FAQ list in Streamlit application.

    Args:
        num_of_rows (int): Number of rows to be displayed in the list

    Returns:
        None
    """
    response = run(endpoints.post_faq_random_questions("faq", num_of_rows))
    faq_list = json.loads(response.text)
    try:
        questions_list = faq_list[0]["result"]
    except Exception as e:
        st_logger.error("Error during loading of faq list: " + str(e))
        st.title(st.session_state.translator("🔍The list is empty"))
        return
    for question in questions_list:
        with st.expander(question["question"]):
            st.write(question["answer"])
            st.button(
                st.session_state.translator("Delete"),
                key=str('faq_delete_question' + question["question"]),
                on_click=on_click_delete_faq_question,
                args=[question["question"]]
            )


def on_click_delete_faq_question(question: str) -> None:
    """
    Button callback that deletes selected faq record from Chroma.

    Args:
        question (str): Question to be deleted

    Returns:

    """
    response = run(endpoints.delete_delete_one_chroma_record(collection_name="faq", filter={"question": question}))
    if endpoints.is_api_call_successful(response):
        st.toast(st.session_state.translator("Delete process finished ✔"))
        st_logger.info(f"Deleted successfully faq: '{question}'")  
    else:
        st_logger.error("Error during deleting of faq: " + question)  
        st.toast(st.session_state.translator("⚠️Error during deleting of FAQ"))
