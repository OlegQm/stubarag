# pylint: disable=consider-using-enumerate
# pylint: disable=broad-exception-caught
"""
Fetches predefined questions based on the provided queries.
"""

import random
import logging
from typing import Dict, Any, List

from chromadb.api import AsyncClientAPI
from fastapi import status

from app.routers.schemas import RandomQuestionResponse, RandomQuestion
from app.utils import initialize_embedding_function

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_message_and_return(
    message: str,
    result: List[RandomQuestion],
    status_code: int
) -> RandomQuestionResponse:
    """
    Logs a message and constructs a structured RandomQuestionResponse object.

    Args:
        message (str): A descriptive message about the operation, e.g., success or error details.
        result (List[RandomQuestion]): The list of random questions or None in case of an error.
        status_code (int): HTTP status code representing the operation's outcome (e.g., 200 for success, 500 for errors).

    Returns:
        RandomQuestionResponse: A structured response containing the message, result, and status code.
    """
    logger.info(message)
    return RandomQuestionResponse(
        message=message,
        result=result,
        status=status_code
    )


async def fetch_random_questions(
    db_client: AsyncClientAPI,
    collection: str,
    random_count: int = 3
) -> RandomQuestionResponse:
    """
    Fetches a specified number of random questions from a given collection in Chroma DB.
    """
    logger.info(f"Attempting to fetch {random_count} random questions from collection: {collection}")

    if not collection:
        return log_message_and_return(
            "Collection name must be provided.",
            [],
            status.HTTP_400_BAD_REQUEST
        )
    if not db_client:
        return log_message_and_return(
            "Database client is not initialized.",
            [],
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    if random_count <= 0:
        return log_message_and_return(
            "Invalid random count. Must be a positive integer.",
            [],
            status.HTTP_400_BAD_REQUEST
        )

    try:
        embedding_function = initialize_embedding_function()
        chroma_collection = await db_client.get_or_create_collection(
            name=collection,
            embedding_function=embedding_function
        )
        logger.info(f"Successfully accessed collection: {collection}")

        all_data = await chroma_collection.get(include=["metadatas"])
        metadatas = all_data.get("metadatas", [])
        logger.info(f"Retrieved {len(metadatas)} metadatas.")

        if not metadatas:
            return log_message_and_return(
                f"No data found in collection '{collection}'.",
                [],
                status.HTTP_404_NOT_FOUND
            )
        if len(metadatas) < random_count:
            random_count = len(metadatas)

        random_indices = random.sample(range(len(metadatas)), random_count)
        random_metadatas = [metadatas[i] for i in random_indices]

        formatted_results = [
            RandomQuestion(
                question=meta.get("question", "N/A"),
                answer=meta.get("answer", "N/A"),
                no=meta.get("no", i + 1),
                doc=meta.get("doc", "N/A"),
                url=meta.get("url", "N/A"),
            )
            for i, meta in enumerate(random_metadatas)
        ]

        logger.info(f"Formatted random results: {formatted_results}")

        return log_message_and_return(
            f"Successfully retrieved {len(formatted_results)} random questions from '{collection}'.",
            formatted_results,
            status.HTTP_200_OK
        )

    except ValueError as ve:
        return log_message_and_return(
            f"ValueError: {str(ve)}",
            [],
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except KeyError as ke:
        return log_message_and_return(
            f"KeyError: {str(ke)}",
            [],
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except TypeError as te:
        return log_message_and_return(
            f"TypeError: {str(te)}",
            [],
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return log_message_and_return(
            f"Error retrieving random questions: {str(e)}",
            [],
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def query_chroma(
    db_client: AsyncClientAPI,
    query: Dict[str, Any]
) -> RandomQuestionResponse:
    """
    Retrieves random questions from a specified collection using the fetch_random_questions function.

    Args:
        db_client (AsyncClientAPI): The Chroma database client used to interact with the collection.
        query (Dict[str, Any]): A dictionary containing:
            - "collection" (str): The name of the collection to query.
            - "random" (int): The number of random questions to fetch. Defaults to 3.

    Returns:
        RandomQuestionResponse: A structured response containing a message, 
            the list of random questions, and the operation's status code.
    """
    collection = query.get("collection")
    random_count = query.get("random", 3)
    if not collection.strip():
        return log_message_and_return(
            "Invalid collection name in query. Must be a non-empty string.",
            [],
            status.HTTP_400_BAD_REQUEST
        )
    if random_count <= 0:
        return log_message_and_return(
            "Invalid random count in query. Must be a positive integer.",
            [],
            status.HTTP_400_BAD_REQUEST
        )
    try:
        return await fetch_random_questions(db_client, collection, random_count)
    except Exception as e:
        return log_message_and_return(
            f"Unexpected error: {str(e)}",
            None,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
