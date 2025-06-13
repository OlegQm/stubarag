import httpx

from common.session.decorators import http_timer

BASE_URL = "http://backend:8080"


# Asynchronous function that retrieve data from ChromaDB
@http_timer
async def get_retrieve_data(
    text: str,
    filename: str = None,
    user: str = None,
    date: str = None,
    n_results: int = None,
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
    }

    # Filter out parameters with None values
    params = {k: v for k, v in params.items() if v is not None}

    # Make an API call to retrieve data
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/retrieve_data", params=params)

    # Return the response
    return response
