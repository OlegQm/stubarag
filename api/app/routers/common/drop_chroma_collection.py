from typing import Annotated

from fastapi import APIRouter, Depends, Query
from chromadb.api import AsyncClientAPI

from app.database import get_chromadb_client
from app.services.common.drop_chroma_collection_service import drop_collection
from app.routers.schemas import DropCollectionResponse

router = APIRouter()

@router.delete(
    "/common/drop_chroma_collection",
    response_model=DropCollectionResponse,
    summary="Permanently delete a ChromaDB collection"
)
async def drop_chroma_collection(
    db_client: Annotated[AsyncClientAPI, Depends(get_chromadb_client)],
    collection_name: Annotated[
        str,
        Query(
            ...,
            description="The name of the ChromaDB collection to drop",
            min_length=1
        )
    ]
) -> DropCollectionResponse:
    """
    Completely drops the ChromaDB collection named `collection_name`.

    - Returns 400 if the name is empty.
    - Returns 404 if the collection does not exist.
    - Returns 200 on successful deletion.
    """
    return await drop_collection(
        db_client=db_client,
        collection_name=collection_name
    )
