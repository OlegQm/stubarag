from typing import Dict, Any

from fastapi import APIRouter, Body

from app.routers.schemas import DeleteRecordResponse
from app.services.common.delete_one_mongo_record_service import delete_record

router = APIRouter()

@router.delete(
    "/common/delete_one_mongo_record",
    response_model=DeleteRecordResponse
)
async def delete_webscraper_record(
    collection_name: str = Body(..., embed=True),
    filter: Dict[str, Any] = Body(..., embed=True),
) -> DeleteRecordResponse:
    """
    Deletes a record from the 'collection_name' MongoDB collection by filter.

    Args:
        filter (Dict[str, Any]): The filter of the record to delete.

    Returns:
        DeleteRecordResponse: Status and message indicating
            the result of the operation.
    """

    return await delete_record(filter, collection_name)
