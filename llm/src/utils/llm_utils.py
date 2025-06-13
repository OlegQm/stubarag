import os
import json
from asyncio import run as arun

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from src.utils.backend_connection import get_retrieve_data
from src.utils.data_models import RagResponse
from common.logging.global_logger import logger

"""

A module for utility functions used by chat workflow.

"""


def get_openai_representation_of_role(role: str) -> str:
    """
    Returns the OpenAI representation of the given role.

    Args:
        - role (str): The role to be converted.

    Returns:
        - str: The OpenAI representation of the given role.

    """
    if role == "human":
        return "user"
    elif role == "ai":
        return "assistant"


# Function that initialize a llm client for a session
def initialize_llm_client(
    model: str = "gpt-4o-mini",
    streaming: bool = True,
    temperature: float = 0,
    top_p: float = 0.8,
) -> ChatOpenAI:
    """
    Initializes and returns a ChatOpenAI client for communication with OpenAI API with the specified parameters.

    Args:
        - model (str): The model name to use for the LLM client. Default is "gpt-4o-mini".
        - streaming (bool): Whether to enable streaming mode. Default is True.
        - temperature (float): The temperature setting for the model, controlling the randomness of the output. Default is 0.
        - top_p (float): The cumulative probability for nucleus sampling. Default is 0.8.

    Returns:
        - ChatOpenAI: An instance of the ChatOpenAI client initialized with the specified parameters.

    """

    # Get the OpenAI API key from the environment variables
    openai_api_key = os.getenv("DEV_OPENAI_KEY")

    try:
        # Initialize the LLM client
        llm = ChatOpenAI(
            model=model,
            api_key=openai_api_key,
            streaming=streaming,
            temperature=temperature,
            top_p=top_p,
        )

        logger.debug(
            f"LLM client ({temperature},{top_p},{streaming}) initialized successfully")

        # Return the initialized LLM client
        return llm

    except Exception as e:
        logger.error(f"Failed to initialize LLM client: {e}")
        return None


def answer_from_chroma(messages: list) -> str:
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


def process_flow_output(final_answer: RagResponse) -> str:
    """
    Processes the output of a RAG (Retrieval-Augmented Generation) response and formats it into a string.

    If the `final_answer` contains sources, the function appends the sources to the answer, separated by a delimiter.
    If no sources are present, it simply returns the answer.

    Args:
        final_answer (RagResponse): An object containing the answer and its associated sources.

    Returns:
        str: A formatted string containing the answer and, if available, its sources.
    """
    try:
        if hasattr(final_answer, "sources") and final_answer.sources != []:
            rag_answer = final_answer.answer + "\n\n---\n\n" + "Source: "
            for i in final_answer.sources:
                if i != final_answer.sources[-1]:
                    rag_answer += (i + ", ")
                else:
                    rag_answer += i
        else:
            rag_answer = final_answer.answer

    except Exception as e:
        logger.error(f"Failed to process RAG response: {e}")
        rag_answer = "Failed to process RAG response."

    return rag_answer


def get_retrieved_context(state: dict) -> str:
    """
    Extracts and formats the retrieved context from the given state dictionary.
    This function iterates over the "context" list in the provided state dictionary,
    retrieves the `retrieved_context` attribute from each context object, and escapes
    curly braces by replacing "{" with "{{" and "}" with "}}". The formatted contexts
    are then returned as a string representation of a list.
    Args:
        -state (dict): A dictionary containing a "context" key, which is expected to
                      be a list of objects with a `retrieved_context` attribute.
    Returns:
        -str: A string representation of a list containing the formatted retrieved
             contexts.
    """
    return str([
        context.retrieved_context.replace("{", "{{").replace("}", "}}")
        for context in state["context"]
    ])


def get_conversation_messages(state: dict) -> str:
    """
    Extracts and processes conversation messages from the given state dictionary,
    formats them for prompt compatibility, and returns the result as a string.
    Args:
        - state (dict): A dictionary containing the conversation state. It must
                    include a "messages" key, which is a list of message objects.
    Returns:
        - str: A string representation of the processed conversation messages,
            formatted to be compatible with prompt requirements.
    Notes:
        - The function identifies the most recent human message in the conversation
        and extracts all messages following it.
        - Each message is processed into a dictionary with "role" and "content" keys.
        - The resulting list of messages is converted to a string with special
        handling to escape curly braces for prompt compatibility.
    """
    raw_conversation_messages = list(reversed(state["messages"]))[
        next(
            (index for index, message in enumerate(
                reversed(state["messages"])) if isinstance(message, HumanMessage)),
            len(state["messages"])
        ):
    ]

    processed_conversation_messages = [
        {"role": message.type, "content": message.content}
        for message in raw_conversation_messages
    ]

    prompt_compatible_conversation_messages = str(
        processed_conversation_messages[:-1]).replace("{", "{{").replace("}", "}}")

    return prompt_compatible_conversation_messages


def get_user_query(state: dict) -> str:
    """
    Extracts the most recent user query from the conversation state.

    Args:
        -state (dict): A dictionary representing the conversation state, 
                      which includes a list of messages.
    Returns:
        -str: The content of the last message in the conversation, 
             assumed to be the user's query.
    """
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            return message.content
    return ""
