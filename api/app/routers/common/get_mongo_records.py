from typing import Dict, Any

from fastapi import APIRouter, Body, Query
from fastapi.responses import JSONResponse

from app.services.common.get_mongo_records_service import get_records

router = APIRouter()

@router.get(
    "/common/get_mongo_records",
)
async def get_mongo_records(
    collection_name: str = Query(
        ...,
        description="Name of the MongoDB collection"
    ),
    filter: Dict[str, Any] = Body(
        ...,
        embed=True,
        description="Filter criteria to find the record"
    )
) -> JSONResponse:
    """
    Retrieves a single document from the specified MongoDB collection using the provided filter.

    This endpoint allows clients to fetch one document based on query criteria passed in the request body.
    The collection name must be passed as a query parameter. If the record is found, it will be returned
    with HTTP 200. If no record matches the filter, HTTP 404 will be returned.

    Args:
        collection_name (str): Name of the MongoDB collection to search in (query parameter).
        filter (Dict[str, Any]): Dictionary representing the filter to apply when searching (request body).

    Returns:
        JSONResponse: A response with status code and either the matched record or an error message.
    """
    return await get_records(
        collection_name=collection_name,
        filter=filter
    )
