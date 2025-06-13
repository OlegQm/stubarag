import streamlit as st

from asyncio import run

from src.utils import rag_endpoints


#Main method of subpage 'Štatistika'
def statistics():

    st.title(st.session_state.translator("📊 Statistics"))

    st.text(st.session_state.translator("Here will be some statistics about RAGbot usage."))

    st.text("Temporary test ground for API endpoints.")

    if "pressed" not in st.session_state:
        st.session_state.pressed = False

    if "ingest_text" not in st.session_state:
        st.session_state.ingest_text = False

    if "retrieve_data" not in st.session_state:
        st.session_state.retrieve_data = False

    if "get_rag_answer" not in st.session_state:
        st.session_state.get_rag_answer = False

    if st.button("get_status"):
        st.session_state.pressed = True
    
    if st.session_state.pressed:
        st.success(run(rag_endpoints.get_status()).text)

    if st.button("test_ingest_text"):
        st.session_state.ingest_text = True

    if st.session_state.ingest_text:
        st.success(run(rag_endpoints.post_ingest_text("Boris lives on planet Earth")).text)

    if st.button("retrieve_data"):
        st.session_state.retrieve_data = True

    if st.session_state.retrieve_data:
        st.success(run(rag_endpoints.get_retrieve_data(text="FEI STU",n_results=2)).text)

    if st.button("get_rag_answer"):
        st.session_state.get_rag_answer = True

    if st.session_state.get_rag_answer:
        st.success(run(rag_endpoints.post_get_rag_answer("Kto je dekan?")).text)

statistics()