from typing import List, Dict, Any, Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from chromadb.api import AsyncClientAPI

from app.database import get_chromadb_client
from app.services.faq.similar_questions_service import query_chroma
from app.routers.schemas import SimilarQuestionResponse

router = APIRouter()

@router.post(
    "/faq/similar_questions",
    response_model=List[SimilarQuestionResponse]
)
async def similar_questions(
    db_client: Annotated[AsyncClientAPI, Depends(get_chromadb_client)],
    queries: List[Dict[str, Any]]
) -> List[SimilarQuestionResponse]:
    """
    Handles requests to find similar questions across multiple collections.

    Args:
        db_client (AsyncClientAPI): The Chroma database client used to execute queries.
        queries (List[Dict[str, Any]]): A list of query dictionaries, each containing:
            - "search" (str): The text of the query for which similar questions are sought.
            - "collection" (str): The name of the collection to search within.
            - "top" (int): The maximum number of similar questions to return (default: 3).
            - "similarity" (float): The minimum similarity threshold for the results (default: 0.985).

    Returns:
        List[SimilarQuestionResponse]: A list of structured responses, one for each query.
    """
    results = []

    for query in queries:
        search = query.get("search", "").strip()
        collection = query.get("collection", "").strip()
        top = query.get("top", 3)
        similarity = query.get("similarity", 0.985)

        if not search:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query cannot be empty."
            )
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Collection name cannot be empty."
            )

        received_questions = await query_chroma(
            db_client=db_client,
            search=search,
            collection=collection,
            top=top,
            similarity=similarity
        )

        if received_questions.status != status.HTTP_200_OK:
            raise HTTPException(
                status_code=received_questions.status,
                detail=received_questions.message
            )

        results.append(received_questions)

    return results
