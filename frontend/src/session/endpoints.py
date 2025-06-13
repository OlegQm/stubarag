from httpx import AsyncClient
from common.session.decorators import http_timer

@http_timer
async def post_faq_random_questions(collection: str, random: int) -> dict:
    """
    Async function that sends a POST request to get random FAQ questions.

    Args:
        collection (str): Name of the collection to get questions from
        random (int): Number of random questions to retrieve

    Returns:
        dict: Response from the endpoint
    """

    BASE_URL = "http://backend:8080"

    body = [{
        "collection": collection,
        "random": random
    }]
    async with AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/faq/random_questions", json=body)
    return response
