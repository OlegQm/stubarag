import streamlit as st
from src.gui.style import create_main_title

"""

A module for creating the authentication page layout for the chat application.

"""


# Function that creates and builds authentication page
def create() -> None:
    """
    Creates the authentication page layout for the chat application.
    This function sets up the layout for the authentication page, including
    language switching buttons and the main title. It uses Streamlit's layout
    components to arrange elements on the page.

    Args:
        None

    Returns:
        None

    Layout:
        - Adds a top spacer.
        - Creates buttons for language switching (Slovak and English).
        - Adds a middle spacer.
        - Displays the main title "FEI STU Chat" centered.
        - Adds a bottom spacer.

    Note:
        - The function imports `set_language` from `chat_app.session.control` to handle
        language switching when the buttons are clicked.
        - The function uses inline HTML for spacing and Streamlit's column layout for
        arranging elements.

    """
    # Just a spacer
    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

    # Create buttons for language switching
    spacer1, col1, col2, spacer2 = st.columns(
        [3, 1, 1, 3], gap="small", vertical_alignment="center"
    )

    # Import at function level to avoid circular imports
    from src.session.control import set_language

    # Create buttons for language switching
    with col1:
        st.button(
            "SK",
            help="Slovenčina",
            on_click=set_language,
            args=("sk",),
            type="secondary",
            key="slovak",
            use_container_width=True,
        )

    with col2:
        st.button(
            "EN",
            help="English",
            on_click=set_language,
            args=("en",),
            type="secondary",
            key="english",
            use_container_width=True,
        )

    # Just a spacer
    st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)

    spacer1, col, spacer2 = st.columns([0.7, 1, 0.625], vertical_alignment="center")

    # Create main title (H1 heading level)
    with col:
        create_main_title("FEI STU Chat", "center")

    # Just a spacer
    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
