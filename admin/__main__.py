import streamlit as st
import os
from PIL import Image

import common.session.authentication as auth
import src.gui.sidebar as sidebar
from src.gui.style import apply_style_navigation,apply_style_logo, apply_style_html_input


# Function that handles login event
def login():

    if st.session_state.guest_mode == "1":
        auth.enable_guest_mode()
    else:
        auth.authenticate_user()

    if st.session_state.authenticated:
        st.rerun()


# Function that handles logout event
def logout():

    if st.session_state.guest_mode != "1":
        auth.logout()
        st.rerun()
    else:
        st.title(st.session_state.translator(":material/logout: Log out is disabled when logged in as _Guest_"))


# Function that configured the application and serves as router for multipage app
def start_app():

    st.logo('.streamlit/sidebar_logo.png', icon_image='.streamlit/page_icon.png')
    apply_style_logo()
    apply_style_html_input()


    # ON LOCALHOST: please add GUEST_MODE variable to your local .env
    # GUEST_MODE=1 -> guest mode enable
    # GUEST_MODE=0 -> authentication enabled
    if "guest_mode" not in st.session_state:
        st.session_state.guest_mode = os.getenv("GUEST_MODE")

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # Set assistant icon for streamlit frontend
    if "assistant_icon" not in st.session_state:
        st.session_state.assistant_icon = Image.open(".streamlit/icon.png")

    page_dict = {}
    if st.session_state.authenticated:
        
        control_panel = st.Page("admin_pages/control_panel.py",title=st.session_state.translator("Control panel"),icon="🖥️",url_path="control-panel",default=True)

        conversations_review = st.Page("admin_pages/conversations_review.py",title=st.session_state.translator("Conversations review"),icon="✅",url_path="conversations-review")

        webscraper = st.Page("admin_pages/webscraper.py",title="Webscraper",icon="🌐",url_path="webscraper")

        faq = st.Page("admin_pages/faq.py",title="FAQ",icon="❓",url_path="faq")

        knowledge_administration = st.Page("admin_pages/knowledge_administration.py",title=st.session_state.translator("Knowledge base"),icon="📚",url_path="knowledge-administration")
            
        history_administration = st.Page("admin_pages/history_administration.py",title=st.session_state.translator("Conversation history"),icon="💭",url_path="history-administration")

        statistics = st.Page("admin_pages/statistics.py",title=st.session_state.translator("Statistics"),icon="📊",url_path="statistics")

        fei_news = st.Page("admin_pages/fei_news.py",title=st.session_state.translator("FEI News"),icon="📰",url_path="fei-news")

        app_management_pages = [control_panel,conversations_review,webscraper,faq,knowledge_administration,history_administration,statistics,fei_news]

        logout_page = st.Page(logout, title=st.session_state.translator("Log out"), icon=":material/logout:")

        account_management_pages = [logout_page]

        page_dict[st.session_state.translator("Chat App Management")] = app_management_pages

        sidebar.create()


    if len(page_dict) > 0:
        pg = st.navigation({f"{st.session_state.user_name}": account_management_pages} | page_dict)
    else:
        pg = st.navigation([st.Page(login)])


    apply_style_navigation()
    pg.run()
            

# Main function call for admin_app
if __name__ == "__main__":

    start_app()

