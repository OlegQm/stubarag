import streamlit as st

from src.gui.style import create_main_title, create_sub_title


def create():

    #Just a spacer
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    #Create buttons for language switching
    spacer1,col1,col2,spacer2 = st.columns([3,1,1,3],gap="small",vertical_alignment="center")

    from src.session.control import set_language

    with col1:
        st.button("SK",help="Slovenčina",on_click=set_language,args=("sk",),type="secondary",key="auth_slovak",use_container_width=True)

    with col2:
        st.button("EN",help="English",on_click=set_language,args=("en",),type="secondary",key="auth_english",use_container_width=True)

    #Just a spacer
    st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)

    spacer1,col,spacer2 = st.columns([0.7,1,0.625],vertical_alignment="center")

    with col:

        create_main_title("FEI STU Chat","center")

    spacer1,col,spacer2 = st.columns([0.8,1,0.8],vertical_alignment="center")

    with col:

        create_sub_title(st.session_state.translator("Admin Interface"),"center","red")

    #Just a spacer
    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)