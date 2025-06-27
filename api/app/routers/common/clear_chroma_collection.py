from typing import Annotated

from fastapi import APIRouter, Depends, Body
from chromadb.api import AsyncClientAPI

from app.database import get_chromadb_client
from app.services.common.clear_chroma_collection_service import clear_collection
from app.routers.schemas import ClearCollectionResponse

router = APIRouter()

@router.delete(
    "/common/clear_chroma_collection",
    response_model=ClearCollectionResponse
)
async def clear_faq_collection(
    db_client: Annotated[AsyncClientAPI, Depends(get_chromadb_client)],
    collection_name: str = Body(..., embed=True)
) -> ClearCollectionResponse:
    """
    Deletes all entries in the 'collection_name' collection in ChromaDB.

    Args:
        db_client (AsyncClientAPI): ChromaDB client instance.
        collection_name (str): name of the collection.

    Returns:
        ClearCollectionResponse: A status and message indicating success or failure.
    """
    return await clear_collection(
        db_client=db_client,
        collection_name=collection_name
    )
