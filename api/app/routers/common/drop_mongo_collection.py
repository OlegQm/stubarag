from fastapi import APIRouter, Query
from app.routers.schemas import DropCollectionResponse
from app.services.common.drop_mongo_collection_service import drop_collection

router = APIRouter()

@router.delete(
    "/common/drop_mongo_collection",
    response_model=DropCollectionResponse,
    summary="Drop (delete) an entire MongoDB collection"
)
async def drop_mongo_collection(
    collection_name: str = Query(
        ...,
        description="The name of the collection to drop",
        min_length=1
    )
) -> DropCollectionResponse:
    """
    Drops the specified collection in MongoDB.

    Args:
        collection_name (str): The name of the collection to drop (from query).

    Returns:
        DropCollectionResponse: Status and message indicating success or failure.
    """
    return await drop_collection(collection_name=collection_name)
