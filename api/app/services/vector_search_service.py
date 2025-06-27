from chromadb.api import AsyncClientAPI

from app.routers.schemas import DocumentResponse, Metadata, QueryResponse
from app.utils import build_query_filter, initialize_embedding_function

"""
This module provides a service for performing vector-based searches on a chromadb database.

"""


async def retrieve_data_from_db(
    db_client: AsyncClientAPI,
    text: str,
    filename: str,
    user: str,
    date: str,
    n_results: int,
    collection_name: str,
) -> QueryResponse:
    """

    Retrieve data from chromadb using vector search.
    This function queries a specified collection in the database using a text input
    and filters based on filename, user, and date. It returns a specified number of
    results, including document contents and their metadata.

    Args:
        db_client (AsyncClientAPI): The asynchronous chromadb client.
        text (str): The text to query in chromadb.
        filename (str): The filename to filter the query (or url in case o webscraper).
        user (str): The user to filter the query (or owner in case of webscraper).
        date (str): The date to filter the query.
        n_results (int): The number of results to return.
        collection_name (str): The name of the collection to query.

    Returns:
        QueryResponse: A response object containing the queried documents and their metadata.

    """
    webscraper_collection_name = "webscraper"
    embedding_function = initialize_embedding_function()
    collection = await db_client.get_collection(
        name=collection_name,
        embedding_function=embedding_function
    )

    if collection_name != webscraper_collection_name:
        query_filter = build_query_filter(
            [("filename", filename), ("user", user), ("date", date)]
        )
    else:
        query_filter = build_query_filter([
            ("url", filename), ("owner", user), ("date", date)
        ])

    try:
        result = await collection.query(
            query_texts=[text],
            n_results=n_results,
            where=query_filter,
            include=["documents", "metadatas"]
        )
    except Exception as e:
        print(f"Error while querying ChromaDB: {e}")
        raise

    documents = []
    if "documents" in result and result["documents"]:
        for doc_content, doc_metadata in zip(
            result["documents"][0],
            result["metadatas"][0]
        ):
            if collection_name != webscraper_collection_name:
                metadata = Metadata(
                    date=doc_metadata.get("date"),
                    filename=doc_metadata.get("filename"),
                    user=doc_metadata.get("user")
                )
            else:
                metadata = Metadata(
                    date=doc_metadata.get("date"),
                    filename=doc_metadata.get("url"),
                    user=doc_metadata.get("owner")
                )
            document = DocumentResponse(
                content=doc_content,
                metadata=metadata
            )
            documents.append(document)

    return QueryResponse(documents=documents)
