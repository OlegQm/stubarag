from typing import List, Dict, Any, Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from chromadb.api import AsyncClientAPI

from app.routers.schemas import RandomQuestionResponse
from app.services.faq.random_questions_service import query_chroma
from app.database import get_chromadb_client

router = APIRouter()

@router.post(
    "/faq/random_questions",
    response_model=List[RandomQuestionResponse]
)
async def random_questions(
    db_client: Annotated[AsyncClientAPI, Depends(get_chromadb_client)],
    queries: List[Dict[str, Any]]
) -> List[RandomQuestionResponse]:
    """
    Retrieves predefined questions based on the provided queries.

    Args:
        db_client (AsyncClientAPI): The asynchronous Chroma DB client used to query the database.
        queries (List[Dict[str, Any]]): A list of dictionaries where each dictionary specifies 
            the collection name and the number of random questions to retrieve.

    Returns:
        List[RandomQuestionResponse]: List of structured responses containing a message, 
            a statuses of the operations, and a lists of retrieved questions.
    """

    results = []
    
    for query in queries:
        result = await query_chroma(db_client=db_client, query=query)
        if result.status != status.HTTP_200_OK:
            raise HTTPException(
                status_code=result.status,
                detail=result.message
            )
        results.append(result)

    return results
