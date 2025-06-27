from app.routers.schemas import DeleteResponse
from app.utils import build_query_filter, initialize_embedding_function
from chromadb.api import AsyncClientAPI
from fastapi import HTTPException, status

"""

This module provides a service for deleting data from a ChromaDB collection.

Functions:
    delete_data_from_chromadb(db_client: AsyncClientAPI, file_name: str, user: str, date: str, collection_name: str) -> List[str]:
        Deletes data from a specified ChromaDB collection based on provided filters.
        Raises an HTTPException if none of 'file_name', 'user', or 'date' are provided.

"""

async def delete_data_from_chromadb(
    db_client: AsyncClientAPI,
    file_name: str,
    user: str,
    date: str,
    collection_name: str,
) -> DeleteResponse:
    """
    Asynchronously deletes data from a ChromaDB collection based on provided filters.

    Args:
        db_client (AsyncClientAPI): The asynchronous client API for interacting with the database.
        file_name (str): The name of the file to filter by.
        user (str): The user to filter by.
        date (str): The date to filter by.
        collection_name (str): The name of the collection from which to delete data.

    Returns:
        DeleteResponse: A response object indicating the result of the delete operation.

    Raises:
        HTTPException: If none of 'file_name', 'user', or 'date' are provided.

    """

    if not any([file_name, user, date]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of 'filename', 'user', or 'date' must be provided.",
        )

    embedding_function = initialize_embedding_function()
    collection = await db_client.get_collection(
        name=collection_name, embedding_function=embedding_function
    )

    query_filter = build_query_filter(
        [("filename", file_name), ("user", user), ("date", date)]
    )

    await collection.delete(where=query_filter)

    return DeleteResponse(message="Data deleted successfully.")
