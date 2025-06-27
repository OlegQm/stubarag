from fastapi import APIRouter, Body
from app.routers.schemas import ClearCollectionResponse
from app.services.common.clear_mongo_collection_service import (
    clear_collection
)

router = APIRouter()

@router.delete(
    "/common/clear_mongo_collection",
    response_model=ClearCollectionResponse
)
async def clear_mongo_collection(
    collection_name: str = Body(..., embed=True)
) -> ClearCollectionResponse:
    """
    Clears the specified collection in MongoDB.

    Args:
        collection_name (str): The name of the collection.

    Returns:
        ClearCollectionResponse: A status and a message indicating success.
    """
    return await clear_collection(collection_name=collection_name)
