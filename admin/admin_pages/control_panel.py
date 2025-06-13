import streamlit as st


def control_panel():

    st.title(st.session_state.translator("🖥️ Control panel of :blue[FEI RAGBOT]"))

    st.text(st.session_state.translator("Welcome to the administration interface of FEI RAGbot app"))


control_panel()