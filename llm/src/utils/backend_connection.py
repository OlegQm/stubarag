import httpx

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

    except Exception as e:
        logger.error(f"Failed to connect to the backend services: {e}")

    return response


@http_timer
async def post_query_lightrag(query: str, conversation_history: list[dict]) -> str:
    """
    Sends a query to the Lightrag API and retrieves the response.
    Args:
        query (str): The query string to be sent to the API.
    Returns:
        str: The response string from the API.
    Raises:
        httpx.RequestError: If there is an issue with the HTTP request.
        KeyError: If the expected "response" key is not found in the API response.
    Notes:
        - The function constructs a predefined API query payload with various parameters.
        - It uses an asynchronous HTTP client to send the request to the Lightrag API endpoint.
        - The response is expected to be in JSON format, and the "response" field is extracted from it.
        - Debug logs are generated before and after the API call.
    """
    payload = {
        "query": query,
        "mode": "hybrid",
        "top_k": 3,
        "only_need_context": True,
        "response_type": "Multiple Paragraphs",
        "max_token_for_text_unit": 500,
        "max_token_for_global_context": 2000,
        "max_token_for_local_context": 2000,
        "conversation_history": conversation_history
    }

    logger.debug("Querying Lightrag...")

    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
        response = await client.post(f"{LIGHTRAG_URL}/query", json=payload)

    try:
        answer = str(response.json()["response"])
    except KeyError:
        logger.error(f"Unexpected response: {response.text}")
        answer = "Failed to get response from Lightrag."
    except Exception as e:
        logger.error(f"Error processing LightRAG response: {e}")
        answer = "Error processing LightRAG response."

    return answer
