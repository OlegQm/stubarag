import streamlit as st

from src.gui.style import apply_style_navigation
from src.session.control import set_language

def create():

    apply_style_navigation()

    with st.sidebar:

        #Create buttons for language switching
        spacer1,col1,col2,spacer2 = st.columns([1.2,1.5,1.5,1.2],gap="small",vertical_alignment="top")

        with col1:
            st.button("SK",help="Slovenčina",on_click=set_language,args=("sk",),type="primary",key="slovak",use_container_width=True)

        with col2:
            st.button("EN",help="English",on_click=set_language,args=("en",),type="primary",key="english",use_container_width=True)