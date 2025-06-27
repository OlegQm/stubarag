import json
from langchain.callbacks.base import BaseCallbackHandler
from gettext import GNUTranslations
from asyncio import run as arun

from common.logging.global_logger import logger
from common.llm_adapters.api_connection import post_get_rag_answer, get_retrieve_data

"""

A module for interconnection between frontend app and LLM container.

"""


class FrontendFlow:
    """
    A class to handle the routing of conversation flows in a frontend application.

    Based on the architecture proposed by Michal Maxian.

    Methods:

        __init__():
            Initializes the FrontendFlow instance.
            Builds a state graph for llm for entire session.

        send_query(conversation_content, phase, llm_memory, stream_handler):
            Routes the conversation content based on the phase and returns the response.

        route(conversation_content, phase, llm_memory, stream_handler):
            Routes the conversation content to the appropriate handler based on the phase.
            - Phase 1: Answers purely from chroma.
            - Phase 2: First query to LLM using RAG.
            - Phase 3: Second query to LLM with enhanced user prompt.
    """

    def __init__(self) -> None:
        logger.debug("Initializing FrontendFlow...")

    def send_query(self, conversation_content: list[dict], phase: int, stream_handler: BaseCallbackHandler, translator: GNUTranslations) -> str:
        """
        Connect to the "send_query" interface in the frontend app.

        This interface was originally implemented in the frontend app to handle user queries.

        Args:
            - conversation_content (list[dict]): The content of the conversation as a list of dictionaries.
            - phase (int): The current phase of the conversation.
            - stream_handler (BaseCallbackHandler): A handler for managing streaming responses.
            - translator (GNUTranslations): An instance of GNUTranslations for handling translations.

        Returns:
            - str: The response from the appropriate handler.

        """

        logger.debug("Processing user query...")

        # Route the user query based on the phase
        response = self.route(conversation_content, phase,
                              stream_handler, translator)

        return response

    def route(self, conversation_content: list[dict], phase: int, stream_handler: BaseCallbackHandler, translator: GNUTranslations) -> str:
        """
        Routes the conversation based on the current phase.

        Args:
            - conversation_content (list[dict]): The content of the conversation so far.
            - phase (int): The current phase of the conversation.
            - stream_handler (BaseCallbackHandler): The handler for streaming responses.
            - translator (GNUTranslations): The translator for translating responses.

        Returns:
            - str: The response generated for the current phase of the conversation.

        Phase Details:
            - Phase 1: Retrieves an answer from ChromaDB and asks the user for confirmation.
            - Phase 2: Invokes the RAG flow for the first query to the LLM.
            - Phase 3: Invokes the RAG flow for the second query to the LLM with enhanced user prompt.
            - Other: Indicates the end of the conversation and prompts the user to start a new conversation.
        """
        #if phase == 1:
        if False:
            # First user prompt
            # Answer is purely from chroma
            # Something in form:
            # "Hey, I found this information in my databases. Is this what are you looking for? ..."
            # Did I answer ? If user response is affirmative, end conversation session.
            # response ="This is a phase 1 of LLM conversation. In this phase, I will try to answer your question using just my knowledge base."

            logger.debug("Phase 1 initiated")

            # Get answer from ChromaDB
            response = self.answer_from_chroma(conversation_content)

            # Add a chatbot direction for user to the response
            response = translator(
                "Hey, I found this information in my databases. Is this what you are looking for? \n\n") + response

            # Stream the response to the user
            stream_handler.on_static_string(response)

            return response

        elif phase == 1 or phase == 2:
            # Second user prompt
            # First query to LLM using RAG
            # Add first user prompt as context
            # Did I answer ? If user response is affirmative, end conversation session.
            # response = "This is a phase 2 of LLM conversation. In this phase, I will try to answer your question using RAG."

            logger.debug("Phase 2 initiated")

            # Display information to the user that you are working
            stream_handler.on_static_string(translator("Researching..."))

            # Query the llm container API
            response = arun(post_get_rag_answer([conversation_content[0], conversation_content[-1]],needs_enhancement=False))

            # Stream the response to the user
            stream_handler.on_static_string(response, erase=True)

            return response

        # elif phase == 3:
        else:
            # Third user prompt
            # Second query to LLM with enhanced user prompt, first and second user prompts as context
            # Did I answer ? If user response is affirmative, end conversation session.
            # response = "This is a phase 3 of LLM conversation. In this phase, I will try to answer your question using RAG."

            logger.debug("Phase 3 initiated")

            # Display information to the user that you are working
            stream_handler.on_static_string(translator("Researching..."))

            # Query the llm container API
            response = arun(post_get_rag_answer((conversation_content[:1]+conversation_content[2:]), needs_enhancement=True))

            # Stream the response to the user
            stream_handler.on_static_string(response, erase=True)

            return response

        # else:
        #     # "End of conversation reached. At the end of the conversation, I will write an email for you to send to the study department."
        #     logger.debug("Conversation reached the end")
        #     stream_handler.on_static_string(translator(
        #         "Conversation reached the end. Please start a new conversation."))
        #     return translator("Conversation reached the end. Please start a new conversation.")

    def answer_from_chroma(self, messages: list) -> str:
        """
        Retrieves and formats an answer from the Chroma database based on the provided messages.

        A special function dedicated to the phase 1 of chatbot flow.

        Args:
            - messages (list): A conversation between chatbot and user.

        Returns:
            - str: A formatted string containing the retrieved information and its source.

        """

        try:
            document = arun(get_retrieve_data(
                messages[-1]["content"], n_results=1))

            embedding = json.loads(document.text)

            logger.debug("Successfuly retrieved documents from Database")

            return (
                embedding["documents"][0]["content"]
                + "\n\n---\n\n"
                + "Source: "
                + embedding["documents"][0]["metadata"]["filename"]
            )

        except Exception as e:
            logger.error(f"Failed to retrieve documents: {e}")
            return "Failed to retrieve documents from Database. Please try again later or continue with another question."
