from chromadb.api import AsyncClientAPI
from fastapi import status
from fastapi.responses import JSONResponse

from app.routers.schemas import DropCollectionResponse

def _make_response(message: str, status_code: int) -> JSONResponse:
    """
    Helper to build a JSONResponse with the given message and HTTP status code.
    """
    payload = DropCollectionResponse(message=message, status=status_code)
    return JSONResponse(content=payload.model_dump(), status_code=status_code)


async def drop_collection(
    db_client: AsyncClientAPI,
    collection_name: str
) -> JSONResponse:
    """
    Drops the specified ChromaDB collection.

    Args:
        db_client: AsyncClientAPI instance for ChromaDB.
        collection_name: Name of the collection to delete.

    Returns:
        JSONResponse containing a message and the appropriate HTTP status code.
    """
    if not collection_name.strip():
        return _make_response(
            message="Invalid collection name. Must be a non-empty string.",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    try:
        existing = await db_client.list_collections()
        if collection_name not in existing:
            return _make_response(
                message=f"Collection '{collection_name}' does not exist.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        await db_client.delete_collection(name=collection_name)

        return _make_response(
            message=f"Collection '{collection_name}' has been dropped.",
            status_code=status.HTTP_200_OK
        )

    except Exception:
        return _make_response(
            message="An unexpected error occurred while processing the request.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
