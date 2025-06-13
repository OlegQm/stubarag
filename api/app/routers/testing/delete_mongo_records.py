from typing import Dict, Any

from fastapi import APIRouter, Body

from app.routers.schemas import DeleteRecordResponse
from app.services.common.delete_one_mongo_record_service import (
    delete_record
)

router = APIRouter()

@router.delete(
    "/testing/delete_records",
    response_model=DeleteRecordResponse
)
async def delete_qna_record(
    filter: Dict[str, Any] = Body(..., embed=True)
) -> DeleteRecordResponse:
    """
    Deletes a records from the 'qna' MongoDB collection by filter.

    Args:
        filter (Dict[str, Any]): The filter of the record to delete.

    Returns:
        DeleteRecordResponse: Status and message indicating
            the result of the operation.
    """
    collection_name = "qna"
    return await delete_record(filter, collection_name)
