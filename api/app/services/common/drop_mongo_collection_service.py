from fastapi import status
from fastapi.responses import JSONResponse

from app.database import mongo_db
from app.routers.schemas import DropCollectionResponse

def _make_response(message: str, status_code: int) -> JSONResponse:
    """
    Helper to build a JSONResponse with the given message and HTTP status code.
    """
    payload = DropCollectionResponse(message=message, status=status_code)
    return JSONResponse(content=payload.model_dump(), status_code=status_code)


async def drop_collection(
    collection_name: str
) -> JSONResponse:
    """
    Drops (deletes) the entire MongoDB collection named `collection_name`.

    Args:
        collection_name (str): The name of the collection to drop.

    Returns:
        JSONResponse:
            FastAPI response with appropriate HTTP status code and message.
    """
    if not collection_name.strip():
        return _make_response(
            message="Invalid collection name. Must be a non-empty string.",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    try:
        existing_collections = mongo_db.list_collection_names()
        if collection_name not in existing_collections:
            return _make_response(
                message=f"Collection '{collection_name}' does not exist.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        collection_to_drop = mongo_db.get_collection_by_name(collection_name)
        collection_to_drop.drop()

        return _make_response(
            message=f"Collection '{collection_name}' has been successfully dropped.",
            status_code=status.HTTP_200_OK
        )

    except Exception:
        return _make_response(
            message="An unexpected error occurred while processing the request.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
