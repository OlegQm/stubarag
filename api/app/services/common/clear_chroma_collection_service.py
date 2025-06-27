from chromadb.api import AsyncClientAPI
from fastapi import status
from fastapi.responses import JSONResponse

from app.utils import initialize_embedding_function
from app.routers.schemas import ClearCollectionResponse

def return_clear_collection_response(
    message: str,
    status: int
) -> JSONResponse:
    response_data = ClearCollectionResponse(
        message=message,
        status=status
    )
    return JSONResponse(
        content=response_data.model_dump(),
        status_code=status
    )

async def clear_collection(
        db_client: AsyncClientAPI,
        collection_name: str
) -> JSONResponse:
    """
    Deletes all entries in the 'collection_name' collection in ChromaDB.

    Args:
        db_client (AsyncClientAPI): ChromaDB client instance.
        collection_name (str): Name of the collection.

    Returns:
        JSONResponse: FastAPI response with correct HTTP status code and message.
    """
    if not collection_name.strip():
        return return_clear_collection_response(
            message="Invalid collection name. Must be a non-empty string.",
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        collections = await db_client.list_collections()
        if collection_name not in collections:
            return return_clear_collection_response(
                message=f"Collection '{collection_name}' does not exist.",
                status=status.HTTP_404_NOT_FOUND
            )

        await db_client.delete_collection(name=collection_name)

        embedding_function = initialize_embedding_function()
        await db_client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function,
            metadata={"hnsw:space": "cosine"}
        )

        return return_clear_collection_response(
            message=f"'{collection_name}' collection has been successfully cleared.",
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return return_clear_collection_response(
            message=f"Unexpected error clearing '{collection_name}' collection: {str(e)}",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
