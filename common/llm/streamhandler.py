from langchain.callbacks.base import BaseCallbackHandler, AsyncCallbackHandler
import time
import asyncio

"""

A module for defining Streamlit callback handlers for LLM agents.

"""


# Displays response in form of stream
class StreamHandler(BaseCallbackHandler):
    """
    A handler class for managing and displaying streaming text updates.

    Attributes:
        - container (object): The container object that has the display method.
        - initial_text (str): The initial text to start with. Defaults to an empty string.
        - display_method (str): The method name of the container to display the text. Defaults to 'markdown'.

    Methods:
        - __init__(self, container, initial_text="", display_method='markdown'): Initializes the StreamHandler object.
        - on_llm_new_token(token: str, **kwargs): Appends a new token to the text and updates the display using the specified method.

    """

    # Initializes the StreamHandler object
    def __init__(
        self,
        container: object,
        initial_text: str = "",
        display_method: str = "markdown",
    ) -> None:

        self.container = container
        self.text = initial_text
        self.display_method = display_method

    # Appends a new token to the text and updates the display using the specified method
    def on_llm_new_token(self, token: str, **kwargs: dict) -> None:

        self.text += token
        display_function = getattr(self.container, self.display_method, None)
        # Verifies display method
        if display_function is not None:
            display_function(self.text)
        else:
            raise ValueError(f"Invalid display_method: {self.display_method}")
        
    def on_static_string(self, string: str, delay: float = 0.0005, erase: bool = False, **kwargs: dict) -> None:
        """
        Appends characters from a static string to the text with a delay and updates the display using the specified method.

        Args:
            - string (str): The static string to be displayed character by character.
            - delay (float): The delay in seconds between each character. Defaults to 0.1 seconds.
        """
        if(erase):
            self.text = ""

        for char in string:
            self.text += char
            display_function = getattr(self.container, self.display_method, None)
            # Verifies display method
            if display_function is not None:
                display_function(self.text)
            else:
                raise ValueError(f"Invalid display_method: {self.display_method}")
            time.sleep(delay)