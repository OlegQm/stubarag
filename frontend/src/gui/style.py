import streamlit as st
import streamlit.components.v1 as components

"""

A module for defining and creating custom styles for the chat application.

"""


# Function that creates a styled title for chat main page
def create_main_title(text: str, align: str = "left") -> None:
    """
    Creates a custom main title (<h1> HTML element) for a chat page using Streamlit.

    This function generates custom CSS and HTML to style and display a main title
    on a chat page. The title is styled using the specified alignment and a fixed color.

    Args:
        - text (str): The text to be displayed as the main title.
        - align (str): The alignment of the title text. Default is "left". Possible values are "left", "center", and "right".

    Returns:
        None

    """

    # Custom CSS style for h1 header (st.title() method in streamlit)
    title_css = f"""

        <style>
        h1 {{
            text-align: {align};
            color: #0039A6 !important;
        }}
        </style>
        """

    st.markdown(title_css, unsafe_allow_html=True)

    # Custom HTML for main title of chat page
    title_html = f"""

        <h1>{text}</h1>
        """

    # Create custom main title for a chat page
    st.markdown(title_html, unsafe_allow_html=True)


# Function that creates header for sidebar
def create_sidebar_header(text: str) -> None:
    """
    Creates a custom sidebar header with the specified text in a Streamlit application.

    This function applies custom CSS styles to an <h2> HTML element to center-align the text,
    change its color, and scale its size.

    Used to create a header for the sidebar history of conversations section.

    Args:
        - text (str): The text to be displayed in the sidebar header.

    Returns:
        None

    """

    # Custom CSS style for h2 header (st.header() method in streamlit)
    header_css = """

        <style>
        h2 {
            text-align: center;
            color: #E6EBF6 !important;
            transform: scale(1.2);
        }
        </style>
        """

    st.markdown(header_css, unsafe_allow_html=True)

    # Custom HTML for sidebar history of conversations section
    sidebar_title_html = f"""

        <h2>
            {text}
        </h2>


        """

    # Create custom sidebar header
    st.markdown(sidebar_title_html, unsafe_allow_html=True)


# Function that defines styles for chat app sidebar
def apply_style_sidebar() -> None:
    """
    Applies custom CSS styling for st.sidebar() method.

    This function injects a CSS style block into the Streamlit app to modify the appearance
    of the sidebar. The sidebar's background color is set to #0039A6, and its contents are
    centered and displayed in a column layout.

    Args:
        None

    Returns:
        None

    """

    # Custom CSS style for st.sidebar() method
    sidebar_css = """

        <style>
        [data-testid=stSidebar] {
            background-color: #0039A6;
            align-items: center;
            display: flex;
            flex-direction: column;
        }
        </style>
        """

    st.markdown(sidebar_css, unsafe_allow_html=True)


# Function that changes size of st.button() element using custom JavaScript
def change_button_size(widget_label: str, size_percent: int) -> None:
    """
    Adjusts the size of a button in a web-based GUI by scaling it to a specified percentage.

    Args:
        - widget_label (str): The label of the button to be resized.
        - size_percent (int): The percentage to scale the button size.

    Returns:
        None

    """

    # Custom JavaScript injection to scale the button size
    htmlstr = f"""
            <script>
                var elements = window.parent.document.querySelectorAll('button');
                for (var i = 0; i < elements.length; ++i) {{
                    if (elements[i].innerText == '{widget_label}') {{
                        elements[i].style.transform = 'scale({size_percent}%)';
                    }}
                }}
            </script>
            """
    components.html(f"{htmlstr}", height=0, width=0)


def apply_faq_style() -> None:
    """
    Applies custom CSS styling for FAQ section in the Streamlit app.

    This function injects a CSS style block into the Streamlit app to modify the appearance
    of the FAQ section. The background color is set to #0039A6, and the text color is set to white.

    Args:
        None

    Returns:
        None

    """

    # Custom CSS style for FAQ section
    faq_css = """

        <style>
        [data-testid=stExpander] {
            background-color: #84BBF8;
            align-items: center;
            display: flex;
            flex-direction: column;
        }
        </style>
        """

    st.markdown(faq_css, unsafe_allow_html=True)