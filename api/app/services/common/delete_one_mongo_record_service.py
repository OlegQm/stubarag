from typing import Dict, Any

from fastapi import status
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError

from app.database import mongo_db
from app.services.common.delete_one_chroma_record_service import (
    return_delete_record_response
)

async def delete_record(
    filter: Dict[str, Any],
    collection_name: str
) -> JSONResponse:
    """
    Deletes a record from the 'collection_name' MongoDB collection by 'filter'.

    Args:
        filter (Dict[str, Any]): The 'filter' of the record to delete.

    Returns:
        DeleteRecordResponse: Status and message indicating
            the result of the operation.
    """

    try:
        if not collection_name.strip():
            return return_delete_record_response(
                message="Collection name is empty",
                status=status.HTTP_400_BAD_REQUEST
            )
        collection = mongo_db.get_or_create_collection(collection_name)
        delete_result = collection.delete_one(filter)

        if delete_result.deleted_count == 0:
            return return_delete_record_response(
                message=f"Record with filter '{filter}' not found in collection '{collection_name}'.",
                status=status.HTTP_404_NOT_FOUND
            )

        return return_delete_record_response(
            message=f"Record with filter '{filter}' successfully deleted from collection '{collection_name}'.",
            status=status.HTTP_200_OK
        )

    except PyMongoError as e:
        return return_delete_record_response(
            message=f"An error occurred while accessing MongoDB: {str(e)}",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return return_delete_record_response(
            message=f"An unexpected error occurred: {str(e)}",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
