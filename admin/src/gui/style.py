import streamlit as st
import streamlit.components.v1 as components


#Function that defines styles for chat app sidebar pages navigation
def apply_style_navigation():

    #Custom CSS style for st.navigation() method
    navbutton_pressed_css = """

        <style>
        .st-emotion-cache-1rtdyuf {
            color: #E6EBF6;
        }
        </style>
        """

    st.markdown(navbutton_pressed_css,unsafe_allow_html=True)

     #Custom CSS style for st.navigation() method
    navbutton_released_css = """

        <style>
        .st-emotion-cache-2s0is {
            color: #E6EBF6;
        }
        </style>
        """

    st.markdown(navbutton_released_css,unsafe_allow_html=True)

    #Custom CSS style for st.navigation() method
    navmenu_header_css = """

        <style>
        .st-emotion-cache-1n7fb9x {
            color: red;
        }
        </style>
        """

    st.markdown(navmenu_header_css,unsafe_allow_html=True)

    #Custom CSS style for st.navigation() method
    logout_icon_css = """

        <style>
        span[data-testid="stIconMaterial"] {
            color: white !important;         
        }
        </style>
        """
    
    st.markdown(logout_icon_css,unsafe_allow_html=True)


#Function that defines styles for sidebar logo and page icon
def apply_style_logo():

    #Custom CSS style for st.logo() method
    logo_size_css = """
        <style>
            img[data-testid="stLogo"] {
                max-width: calc(259px - 1.5rem);
                height: 4rem;
            }
        </style>
        """
    
    st.markdown(logo_size_css,unsafe_allow_html=True)


#Function that defines styles for st.file_uploader()
def apply_style_file_uploader(webscraper:bool=False):

    #Custom CSS style for  st.file_uploader() method
    uploader_css = """

        <style>
        .st-emotion-cache-1fttcpj {
            color: #E6EBF6;
        }
        </style>
        """

    st.markdown(uploader_css,unsafe_allow_html=True)

    #Custom CSS style for  st.file_uploader() method
    uploader_info_css = """

        <style>
        .st-emotion-cache-1u5bms5 {
            color: #abdbe3;
        }
        </style>
        """

    st.markdown(uploader_info_css,unsafe_allow_html=True)

    #Custom CSS style for  st.file_uploader() method
    uploader_icon_css = """

        <style>
        svg {
            fill: #E6EBF6 !important;
        }
        </style>
        """

    st.markdown(uploader_icon_css,unsafe_allow_html=True)

    #CSS mask for multilingual support in uploadere widgets
    uploader_translate_css = """

        <style>
            div[data-testid="stFileUploader"] > section[data-testid="stFileUploaderDropzone"] > button[data-testid="baseButton-secondary"] {
                color: white !important; /* Original text is displayed, but it is white */
                background-color: white !important; 
                padding: 10px 30px; 
                font-size: 16px; 
                border: 1px solid #262730 !important; 
                border-radius: 5px; 
                cursor: pointer; 
                width: auto; 
                display: inline-block; 
                text-align: center; 
                position: relative; 
            }
            div[data-testid="stFileUploader"] > section[data-testid="stFileUploaderDropzone"] > button[data-testid="baseButton-secondary"]::after {
                content: "BUTTON_TEXT";
                color: #0039A6 !important;
                display: block;
                position: absolute;
                top: 50%; 
                left: 50%; 
                transform: translate(-50%, -50%);
                width: 100%;
                text-align: center; 
                pointer-events: none; 
            }
            div[data-testid="stFileUploaderDropzoneInstructions"]>div>span {
               visibility:hidden;
               color: #E6EBF6 !important;
            }
            div[data-testid="stFileUploaderDropzoneInstructions"]>div>span::after {
               content:"INSTRUCTIONS_TEXT";
               visibility:visible;
               display:block;
            }
             div[data-testid="stFileUploaderDropzoneInstructions"]>div>small {
               visibility:hidden;
            }
            div[data-testid="stFileUploaderDropzoneInstructions"]>div>small::before {
               content:"FILE_LIMITS";
               visibility:visible;
               display:block;
            }
         </style>
        """.replace("BUTTON_TEXT", st.session_state.translator("Browse files")).replace("INSTRUCTIONS_TEXT", st.session_state.translator("Drag and drop file here")).replace("FILE_LIMITS", st.session_state.translator("Limit 200MB per file")+(" · CSV" if webscraper else " · PDF, JSON"))

    st.markdown(uploader_translate_css, unsafe_allow_html=True)


#Function that changes size of st.button() element using custom JavaScript
def change_button_size(widget_label,size_percent):
        
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


#Function that creates a styled title for chat main page
def create_main_title(text,align="left",color="#0039A6"):
      
    #Custom CSS style for h1 header (st.title() method in streamlit)
    title_css = f"""

        <style>
        h1 {{
            text-align: {align} !important;
            color: {color} !important;
        }}
        </style>
        """
    
    st.markdown(title_css,unsafe_allow_html=True)
    
    #Custom HTML for main title of chat page
    title_html =f"""

        <h1>{text}</h1>
        """

    #Create custom main title for a chat page
    st.markdown(title_html,unsafe_allow_html=True)


    #Function that creates a styled title for chat main page
def create_sub_title(text,align="left",color="#0039A6"):
      
    #Custom CSS style for h1 header (st.title() method in streamlit)
    title_css = f"""

        <style>
        h2 {{
            text-align: {align};
            color: {color} !important;
        }}
        </style>
        """
    
    st.markdown(title_css,unsafe_allow_html=True)
    
    #Custom HTML for main title of chat page
    title_html =f"""

        <h2>{text}</h2>
        """

    #Create custom main title for a chat page
    st.markdown(title_html,unsafe_allow_html=True)


#Custom CSS style for html <input> tag
def apply_style_html_input():
    """
    Applies custom CSS styles to HTML input elements in a Streamlit application.

    This function injects a <style> block into the Streamlit app's HTML to:
    - Set the background color of input elements to white.
    - Set the border of div elements with the attribute data-baseweb="input" to a specific color.
    
    Args:
        None
    Returns:
        None
    """
     
    html_input_css = """

        <style>
        input {
            background-color: #FFFFFF !important;
        }
        div[data-baseweb="input"] {
            border: 0.5px solid #262730 !important;
        }
        </style>
        """
    
    st.markdown(html_input_css,unsafe_allow_html=True)