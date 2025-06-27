import streamlit as st


# Displays title and navigation elements
def details_page_header():
    st.title(st.session_state.translator("Document details"))
    if st.button(st.session_state.translator("Back")):
        st.session_state.details_row_index_knowledge = None
        st.session_state.display_details_page_knowledge = False
        st.rerun()


# Displays actual details of given conversation
def details_page_body():
    st.title("Item index: "+str(st.session_state.details_row_index_knowledge))
    st.write("File will be displayed here")
