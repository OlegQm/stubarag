from typing import Any, Dict

from fastapi import status
from fastapi.responses import JSONResponse
from chromadb.api import AsyncClientAPI

from app.utils import initialize_embedding_function
from app.routers.schemas import DeleteRecordResponse

def return_delete_record_response(
    message: str,
    status: int
) -> JSONResponse:
    response_data = DeleteRecordResponse(
        message=message,
        status=status
    )
    return JSONResponse(
        content=response_data.model_dump(),
        status_code=status
    )

async def delete_record(
    db_client: AsyncClientAPI,
    collection: str,
    filter: Dict[str, Any]
) -> DeleteRecordResponse:
    """
    Deletes a single record in the ChromaDB 'collection' collection by 'filter'.

    Args:
        db_client (AsyncClientAPI): ChromaDB async client.
        collection (str): Name of the collection to interact with.
        filter (Dict[str, Any]): The filter to use to find the record to delete.

    Returns:
        DeleteRecordResponse: Message about the success of the deletion.
    """
    if len(filter) == 0:
        return return_delete_record_response(
            message="Filter cannot be empty.",
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not collection.strip():
        return return_delete_record_response(
            message="Collection name is empty",
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        embedding_function = initialize_embedding_function()
        chroma_collection = await db_client.get_or_create_collection(
            name=collection,
            embedding_function=embedding_function,
            metadata={"hnsw:space": "cosine"}
        )

        query_result = await chroma_collection.get(where=filter)
        record_count = len(query_result.get("ids", []))

        if record_count > 0:
            await chroma_collection.delete(where=filter)
            return return_delete_record_response(
                message=f"Successfully deleted record(s) with filter: '{filter}'.",
                status=status.HTTP_200_OK
            )
        return return_delete_record_response(
            message=f"No records found to delete for filter: '{filter}'.",
            status=status.HTTP_404_NOT_FOUND
        )

    except Exception as e:
        return return_delete_record_response(
            message=f"Error deleting record: {str(e)}",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
