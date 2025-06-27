from bson import ObjectId
from typing import Optional, Dict, Any, List

from fastapi import status
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError

from app.database import mongo_db


def convert_object_ids_in_list(
    documents: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Converts ObjectId fields in a list of documents to strings for JSON serialization.
    """
    return [
        {
            key: str(value)
            if isinstance(value, ObjectId)
            else value
            for key, value in doc.items()
        } for doc in documents
    ]


def return_get_record_response(
    status: int,
    message: str,
    record: Optional[List[Dict[str, Any]]] = None,
) -> JSONResponse:
    """
    Constructs and returns a JSONResponse object with the given status,
        message, and optional list of records.
    """
    return JSONResponse(
        status_code=status,
        content={
            "message": message,
            "status": status,
            "records": record or []
        }
    )


async def get_records(
    collection_name: str,
    filter: Dict[str, Any]
) -> JSONResponse:
    """
    Searches for documents in the specified MongoDB collection using the provided filter.
    Returns a list of matching documents.
    """
    try:
        if not collection_name.strip():
            return return_get_record_response(
                status=status.HTTP_400_BAD_REQUEST,
                message="Collection name is empty"
            )

        if not isinstance(filter, dict) or not filter:
            return return_get_record_response(
                status=status.HTTP_400_BAD_REQUEST,
                message="Filter must be a non-empty dictionary"
            )

        collection = mongo_db.get_or_create_collection(collection_name)
        cursor = collection.find(filter)
        records = list(cursor)

        if not records:
            return return_get_record_response(
                status=status.HTTP_404_NOT_FOUND,
                message=f"No records found in collection '{collection_name}' matching filter: {filter}"
            )

        records = convert_object_ids_in_list(records)

        return return_get_record_response(
            status=status.HTTP_200_OK,
            message=f"{len(records)} record(s) retrieved successfully from collection '{collection_name}'.",
            record=records
        )

    except PyMongoError as e:
        return return_get_record_response(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"MongoDB error: {str(e)}"
        )

    except Exception as e:
        return return_get_record_response(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Unexpected error: {str(e)}"
        )
