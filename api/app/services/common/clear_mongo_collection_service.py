from fastapi import status
from fastapi.responses import JSONResponse

from app.database import mongo_db
from app.services.common.clear_chroma_collection_service import (
    return_clear_collection_response
)

async def clear_collection(
    collection_name: str
) -> JSONResponse:
    """
    Clears the specified collection in MongoDB.

    Args:
        collection_name (str): The name of the collection.

    Returns:
        JSONResponse: FastAPI response with correct HTTP status code and message.
    """
    try:
        if not collection_name.strip():
            return return_clear_collection_response(
                message="Collection name is empty",
                status=status.HTTP_404_NOT_FOUND
            )

        collection = mongo_db.get_collection_by_name(collection_name)
        if collection is None:
            return return_clear_collection_response(
                message="Collection doesn't exist",
                status=status.HTTP_404_NOT_FOUND
            )
        result = collection.delete_many({})
        return return_clear_collection_response(
            message=f"Deleted {result.deleted_count} documents from '{collection_name}' collection.",
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return return_clear_collection_response(
            message=f"A problem occurred when clearing the collection: {e}",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
