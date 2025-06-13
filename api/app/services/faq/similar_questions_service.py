# pylint: disable=consider-using-enumerate

"""
This module defines utilities and endpoints for retrieving similar questions 
from Chroma DB collections based on specified criteria such as similarity and top results.
"""
from typing import List
import logging

from fastapi import APIRouter, status
from chromadb.api import AsyncClientAPI

from app.routers.schemas import SimilarQuestionResponse, SimilarQuestion
from app.utils import initialize_embedding_function

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_message_and_return(
    message: str,
    result: List[SimilarQuestion],
    status_code: int
) -> SimilarQuestionResponse:
    """
    Constructs a SimilarQuestionResponse object with a given message, result, and status code.

    Args:
        message (str): A descriptive message about the operation (e.g., success or error details).
        result (List[SimilarQuestion]): A list of SimilarQuestion objects to include in the response.
        status_code (int): HTTP status code representing the operation's outcome.

    Returns:
        SimilarQuestionResponse: A structured response object containing the message, result, and status code.
    """
    logger.info(message)
    return SimilarQuestionResponse(
        message=message,
        result=result,
        status=status_code
    )


async def query_chroma(
    db_client: AsyncClientAPI,
    search: str,
    collection: str,
    top: int,
    similarity: float
) -> SimilarQuestionResponse:
    """
    Searches for the most similar questions in a specified collection in Chroma DB.

    Args:
        db_client (AsyncClientAPI): The Chroma database client used to interact with the collection.
        search (str): The text to search for similar questions.
        collection (str): The name of the collection to query.
        top (int): The maximum number of similar questions to retrieve.
        similarity (float): The minimum similarity threshold for a question to be included (0 to 1).

    Returns:
        SimilarQuestionResponse: A structured response containing a list of similar questions and a message.
    """
    if not search.strip():
        return log_message_and_return(
            "Search query cannot be empty.",
            [],
            status.HTTP_400_BAD_REQUEST
        )

    if not collection.strip():
        return log_message_and_return(
            "Invalid collection name. Must be a non-empty string.",
            [],
            status.HTTP_400_BAD_REQUEST
        )

    if top <= 0:
        return log_message_and_return(
            "Invalid top value. Must be a positive integer.",
            [],
            status.HTTP_400_BAD_REQUEST
        )
    
    if not (0 <= similarity <= 1):
        return log_message_and_return(
            "Invalid similarity value. Must be a number between 0 and 1.",
            [],
            status.HTTP_400_BAD_REQUEST
        )

    try:
        embedding_function = initialize_embedding_function()

        chroma_collection = await db_client.get_or_create_collection(
            name=collection,
            embedding_function=embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Successfully accessed collection: {collection}")
    except Exception as e:
        return log_message_and_return(
            f"Error accessing collection '{collection}': {str(e)}",
            [],
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    try:
        query_results = await chroma_collection.query(
            query_texts=[search],
            n_results=top * 2,
            include=["metadatas", "distances"],
        )
        logger.info(f"Query results: {query_results}")
    except Exception as e:
        return log_message_and_return(
            f"Error querying collection '{collection}': {str(e)}",
            [],
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    formatted_results = []
    results_count = 0
    metadatas = query_results.get("metadatas", [[]])[0]
    distances = query_results.get("distances", [[]])[0]

    for i in range(len(metadatas)):
        distance_value = distances[i]
        similarity_score = 1 - (distance_value / 2)

        if similarity_score >= similarity:
            metadata = metadatas[i]
            formatted_results.append(
                SimilarQuestion(
                    question=metadata.get("question", "N/A"),
                    answer=metadata.get("answer", "N/A"),
                    no=metadata.get("no", i + 1),
                    doc=metadata.get("doc", "N/A"),
                    url=metadata.get("url", "N/A"),
                )
            )
            results_count += 1

        if results_count >= top:
            break

    return log_message_and_return(
        f"Retrieved {results_count}/{top} similar questions from collection '{collection}'.",
        formatted_results,
        status.HTTP_200_OK
    )
