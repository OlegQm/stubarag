from langchain_core.tools import tool
from langgraph.types import Command
from langchain_core.tools.base import InjectedToolCallId
from langchain_core.messages import ToolMessage

from src.utils.backend_connection import get_retrieve_data
from src.utils.data_models import RetrieverResponse
from asyncio import run as arun
from typing_extensions import Annotated

from common.logging.global_logger import logger

"""

A module for defining tools that can be used by LLM agents.

"""


@tool
def webscrapes_retriever(retrieve_prompt: str, tool_call_id: Annotated[str, InjectedToolCallId]) -> Command:
    """
    Retrieves embeddings from backend ChromaDB **webscraper** collection based on the provided prompt.

    !!! Retrieval is successful only if name of the faculty or university is not 
    referenced in the 'retrieve_prompt'. !!!

    Usage:
        How to create a 'retrieve_prompt':
        - Focus on conversation direction and the context of the conversation.
        - Be talkative, use a lot of **SLOVAK** synonyms and related terms.
        - Use specific **SLOVAK** terms related to the study and education.

    Examples:
        - User: Kto je dekan?
            'retrieve_prompt': "vedenie fakulty, dekan, e-mail, tel., kancelária"

    Args:
        - retrieve_prompt (str): The prompt used to retrieve embeddings.

    Returns:
        - response: The retrieved embeddings if successful.
        - str: "Failed to retrieve documents" if an exception occurs.
    """

    try:
        logger.debug(f"Retrieving embeddings from webscraper collection...")
        response = arun(get_retrieve_data(retrieve_prompt,
                        n_results=10, collection_name="webscraper"))
        logger.debug(f"Retrieved embeddings: {response.text}")

        return Command(
            update={
                "context": [RetrieverResponse(retrieved_context=response.text)],
                "messages": [
                    ToolMessage(
                        "Successfully retrieved webscrapes.", tool_call_id=tool_call_id
                    )
                ],
            }
        )

    except Exception as e:
        logger.error(f"Failed to retrieve embeddings: {e}")
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        "Failed to retrieve webscrapes.", tool_call_id=tool_call_id
                    )
                ],
            }
        )
