from langchain_core.tools import tool

from common.llm.backend_connection import get_retrieve_data
from asyncio import run as arun

from common.logging.global_logger import logger

"""

A module for defining tools that can be used by LLM agents.

"""

# Uses "retrieve_data" endpoint to retrieve embeddings from the backend ChromaDB.
# Docstring is modified to be comprehensible for LLM agent.
@tool
def documents_retriever_mimic_prompt(retrieve_prompt: str) -> str:
    """
    Retrieves embeddings from backend ChromaDB **knowledge** collection based on the provided prompt.

    !!! Retrieval is successful only if name of the faculty or university is not 
    referenced in the 'retrieve_prompt'. !!!

    Usage:
        How to create a 'retrieve_prompt':
        - a more detailed, talkative Slovak sentence (or multiple sentences) that imitate the 
        language and style of official documents. 
        - Generated senteces should be contradictive to cover as much possibilities as possible.
        - Limit for the prompt is **two sentences**.

    Args:
        - retrieve_prompt (str): The prompt used to retrieve embeddings.

    Examples:
    - User: Sú cvičenia povinné ?
        'retrieve_prompt': "Účasť na cvičeniach je povinná. Študent je povinný sa zúčastniť cvičení. 
        Účasť na cvičeniach je nutná pre získanie kreditov. Účasť na cvičeniach je dobrovoľná."

    Returns:
        - response: The retrieved embeddings if successful.
        - str: "Failed to retrieve documents" if an exception occurs.
    """

    try:
        response = arun(get_retrieve_data(retrieve_prompt, n_results=2, collection_name="knowledge"))
        logger.debug(f"Retrieved embeddings: {response.text}")
        return response.text

    except Exception as e:
        logger.error(f"Failed to retrieve embeddings: {e}")
        return "Failed to retrieve documents"
    

@tool
def documents_retriever_keywords_prompt(retrieve_prompt: str) -> str:
    """
    Retrieves embeddings from backend ChromaDB **knowledge** collection based on the provided prompt.
    
    !!! Retrieval is successful only if name of the faculty or university is not 
    referenced in the 'retrieve_prompt'. !!!

    Usage:
        How to create a 'retrieve_prompt':
        - Focus on conversation direction and the context of the conversation.
        - Be talkative, use a lot of **SLOVAK** synonyms and related terms.
        - Use specific **SLOVAK** terms related to the study and education.

    Examples:
        - User: Kto je dekan?
            'retrieve_prompt': "základné údaje, dekan, e-mail, tel., kancelária"

    Args:
        - retrieve_prompt (str): The prompt used to retrieve embeddings.

    Returns:
        - response: The retrieved embeddings if successful.
        - str: "Failed to retrieve documents" if an exception occurs.
    """

    try:
        response = arun(get_retrieve_data(retrieve_prompt, n_results=2, collection_name="knowledge"))
        logger.debug(f"Retrieved embeddings: {response.text}")
        return response.text

    except Exception as e:
        logger.error(f"Failed to retrieve embeddings: {e}")
        return "Failed to retrieve documents"


@tool
def webscrapes_retriever(retrieve_prompt: str) -> str:
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
        response = arun(get_retrieve_data(retrieve_prompt, n_results=2, collection_name="webscraper"))
        logger.debug(f"Retrieved embeddings: {response.text}")
        return response.text

    except Exception as e:
        logger.error(f"Failed to retrieve embeddings: {e}")
        return "Failed to retrieve documents"