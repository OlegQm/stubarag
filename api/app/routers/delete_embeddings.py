from typing import Annotated, Optional

from app.config import settings
from app.database import get_chromadb_client
from app.routers.schemas import DeleteResponse
from app.services.delete_embeddings_service import delete_data_from_chromadb
from chromadb.api import AsyncClientAPI
from fastapi import APIRouter, Depends, Query, status

"""

This module defines an API endpoint for deleting data from a ChromaDB collection.

"""


CHROMA_COLLECTION_NAME = settings.chroma_collection_name

router = APIRouter()


@router.delete("/delete_data", status_code=status.HTTP_200_OK)
async def retrieve_data(
    db_client: Annotated[AsyncClientAPI, Depends(get_chromadb_client)],
    file_name: Optional[str] = Query("", description="Optional file_name"),
    user: Optional[str] = Query("", description="Optional user"),
    date: Optional[str] = Query("", description="Optional date"),
) -> DeleteResponse:
    """
    This endpoint allows the deletion of data from the ChromaDB based on optional query parameters such as file_name, user, and date.

    Args:
        db_client (AsyncClientAPI): The ChromaDB client instance.
        file_name (Optional[str]): Optional file name to filter the data to be deleted.
        user (Optional[str]): Optional user to filter the data to be deleted.
        date (Optional[str]): Optional date to filter the data to be deleted.

    Returns:
        DeleteResponse: The response indicating the result of the delete operation.

    """

    return await delete_data_from_chromadb(
        db_client=db_client,
        file_name=file_name,
        user=user,
        date=date,
        collection_name=CHROMA_COLLECTION_NAME,
    )
