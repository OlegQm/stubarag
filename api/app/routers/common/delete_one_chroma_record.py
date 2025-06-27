from typing import Annotated, Dict, Any

from fastapi import APIRouter, Depends, Body
from chromadb.api import AsyncClientAPI

from app.routers.schemas import DeleteRecordResponse
from app.database import get_chromadb_client
from app.services.common.delete_one_chroma_record_service import delete_record

router = APIRouter()

@router.delete(
    "/common/delete_one_chroma_record",
    response_model=DeleteRecordResponse
)
async def delete_record_by_url(
    db_client: Annotated[AsyncClientAPI, Depends(get_chromadb_client)],
    collection_name: str = Body(..., embed=True),
    filter: Dict[str, Any] = Body(..., embed=True)
) -> DeleteRecordResponse:
    """
    Deletes a single record in the ChromaDB 'collection_name' collection by 'filter'.

    Args:
        db_client (AsyncClientAPI): ChromaDB async client.
        collection_name (str): Name of the collection to interact with.
        filter (Dict[str, Any]): The url of the page to delete.

    Filter:
        The filter to use to find the record to delete.
        This parameter is passed in the body of the request.
        This is actually the key of the record to be deleted,
            the keys and example queries for the 'faq' and 'webscraper' collections are shown below:

        For the 'faq' collection:
        - key: 'question';
        - request body:
            {"collection_name": "faq", "filter": {"question": "What is ChromaDB?"}}

        For the 'webscraper' collection:
        - key: 'url';
        - request body:
            {"collection_name": "webscraper", "filter": {"url": "https://www.example.com"}}

    Returns:
        DeleteRecordResponse: Message about the success of the deletion.
    """
    return await delete_record(db_client, collection_name, filter)
