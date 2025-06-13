from fastapi import APIRouter, Depends, Query, status
from chromadb.api import AsyncClientAPI
from typing import Annotated, Optional

from app.config import settings
from app.database import get_chromadb_client
from app.routers.schemas import QueryResponse
from app.services.vector_search_service import retrieve_data_from_db

"""

This module defines the API routes for vector search operations using FastAPI.


Endpoint:
- `retrieve_data`: Retrieves data from the vector database based on the provided text query
    and optional filters such as filename, user, date, and the number of results to return.

Configuration:
- `CHROMA_COLLECTION_NAME`: The name of the collection in the ChromaDB database, sourced from settings.

"""

CHROMA_COLLECTION_NAME = settings.chroma_collection_name

router = APIRouter()

@router.get("/retrieve_data", status_code=status.HTTP_200_OK)
async def retrieve_data(
    db_client: Annotated[AsyncClientAPI, Depends(get_chromadb_client)],
    text: Annotated[str, Query(..., description="The text to query")],
    filename: Optional[str] = Query("", description="Optional filename"),
    user: Optional[str] = Query("", description="Optional user"),
    date: Optional[str] = Query("", description="Optional date"),
    n_results: Optional[int] = Query(
        1, description="Number of results to return"),
    collection_name: Optional[str] = Query(
        CHROMA_COLLECTION_NAME,
        description="Optional collection name"
    )
) -> QueryResponse:
    """
    Retrieve data from the chromadb database based on the provided query parameters.

    Args:
        db_client (Annotated[AsyncClientAPI, Depends(get_chromadb_client)]): The database client dependency.
        text (Annotated[str, Query(..., description="The text to query")]): The text to query.
        filename (Optional[str], optional): Optional filename to filter the query. Defaults to "".
        user (Optional[str], optional): Optional user to filter the query. Defaults to "".
        date (Optional[str], optional): Optional date to filter the query. Defaults to "".
        n_results (Optional[int], optional): Number of results to return. Defaults to 1.

    Returns:
        QueryResponse: The response containing the query results.

    """

    return await retrieve_data_from_db(
        db_client=db_client,
        text=text,
        filename=filename,
        user=user,
        date=date,
        n_results=n_results,
        collection_name=collection_name,
    )
