import httpx
from typing import Optional

from common.session.decorators import http_timer
from common.logging.global_logger import logger

BACKEND_URL = "http://backend:8080"
LIGHTRAG_URL = "http://lightrag:9621"

"""

A module for connection to the backend API services.

"""


# Asynchronous function that retrieve data from ChromaDB
@http_timer
async def get_retrieve_data(
    text: str,
    filename: str = None,
    user: str = None,
    date: str = None,
    n_results: int = None,
    collection_name: str = None
) -> httpx.Response:
    """
    Asynchronously retrieves data based on the provided parameters.

    Args:
        - text (str): The prompt for embeddings retrieval.
        - filename (str, optional): The name of the file to filter the results. Defaults to None.
        - user (str, optional): The user to filter the results. Defaults to None.
        - date (str, optional): The date to filter the results. Defaults to None.
        - n_results (int, optional): The number of results to retrieve. Defaults to None.

    Returns:
        - response (httpx.Response): The response object from the API call.

    """

    # Prepare query parameters
    params = {
        "text": text,
        "filename": filename,
        "user": user,
        "date": date,
        "n_results": n_results,
        "collection_name": collection_name
    }

    # Filter out parameters with None values
    params = {k: v for k, v in params.items() if v is not None}

    try:
        # Make an API call to retrieve data
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BACKEND_URL}/api/retrieve_data", params=params)
        # Return the response
        return response

    except Exception as e:
        logger.error(f"Failed to connect to the backend services: {e}")
        return "Failed to connect to the backend services."


@http_timer
async def post_similar_questions(
    search: str,
    collection: str = "knowledge",
    top: Optional[int] = 1,
    similarity: Optional[float] = 0.985
) -> httpx.Response:
    """
    Asynchronously retrieves the top similar questions based on the provided parameters.

    Args:
        - search (str): The search term for retrieving similar questions.
        - collection (str): The collection to search within.
        - top (Optional[int]): The number of top results to retrieve. Defaults to None.
        - similarity (Optional[float]): The similarity threshold. Defaults to None.

    Returns:
        - response (httpx.Response): The response object from the API call.
    """

    # Construct the query JSON
    query = {
        "search": search,
        "collection": collection,
        "top": top,
        "similarity": similarity
    }

    # Remove keys with None values
    query = {k: v for k, v in query.items() if v is not None}

    # Wrap the query in a list as the endpoint expects a list of queries
    payload = [query]

    # Endpoint URL
    endpoint = f"{BACKEND_URL}/api/similar_questions"

    try:
        # Make an API call to post the query
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, json=payload)

        # Return the response
        return response

    except Exception as e:
        logger.error(f"Failed to connect to the backend services: {e}")
        return "Failed to connect to the backend services."