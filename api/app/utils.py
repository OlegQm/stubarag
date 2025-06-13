import uuid

from datetime import date
from typing import Any, Dict, List, Tuple

from app.config import settings
from chromadb.api import AsyncClientAPI
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from langchain_text_splitters import RecursiveCharacterTextSplitter, TextSplitter

"""

This module provides utility functions for working with text embeddings and
interacting with a ChromaDB collection. It includes functions for initializing
an embedding function, splitting text into chunks, building query filters, and
adding split documents to a ChromaDB collection.

Global variables:
    OPENAI_API_KEY (str): The API key for OpenAI.
    EMBEDDING_MODEL (str): The model name for the embedding function.
    CHROMA_COLLECTION_NAME (str): The name of the ChromaDB collection.
    DEV_USER (str): The developer user identifier.
    text_splitter (TextSplitter): An instance of RecursiveCharacterTextSplitter
        for splitting text into chunks.

"""

# Load environment variables
OPENAI_API_KEY = settings.openai_api_key
EMBEDDING_MODEL = settings.embedding_model
CHROMA_COLLECTION_NAME = settings.chroma_collection_name
DEV_USER = settings.dev_user


def initialize_embedding_function() -> OpenAIEmbeddingFunction:
    """
    Initializes and returns an instance of OpenAIEmbeddingFunction.

    This function creates an OpenAIEmbeddingFunction object using the provided
    API key and model name. The API key and model name are expected to be 
    available as global variables OPENAI_API_KEY and EMBEDDING_MODEL, respectively.

    Returns:
        OpenAIEmbeddingFunction: An instance of OpenAIEmbeddingFunction initialized
        with the specified API key and model name.

    """
    return OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name=EMBEDDING_MODEL
    )


"""
text_splitter (TextSplitter): An instance of RecursiveCharacterTextSplitter for splitting text into chunks.

This global variable is initialized with specific parameters to control the chunk size, overlap, and length function.
It is used to split large text documents into smaller, manageable chunks for further processing, such as embedding
or querying.

Attributes:
    chunk_size (int): The maximum size of each text chunk.
    chunk_overlap (int): The number of characters that overlap between consecutive chunks.
    length_function (Callable[[str], int]): A function to calculate the length of a text chunk.
    is_separator_regex (bool): A flag indicating whether the separator is a regular expression.
    
"""
text_splitter: TextSplitter = RecursiveCharacterTextSplitter(
    chunk_size=900,
    chunk_overlap=450,
    length_function=len,
    is_separator_regex=False,
)


def build_query_filter(params: List[Tuple[str, Any]]) -> Dict[str, Any]:
    """
    Constructs a query filter dictionary from a list of key-value pairs.
    
    Args:
        params (List[Tuple[str, Any]]): A list of tuples where each tuple contains a key (str) and a value (Any).

    Returns:
        Optional[Dict[str, Any]]: A dictionary representing the query filter or None if no conditions are present.
    """
    print(f"Received params for filter: {params}")

    query_filter = None
    conditions = [{key: {"$eq": value}} for key, value in params if value]
    conditions_length = len(conditions)

    if conditions_length > 1:
        query_filter = {"$and": conditions}
    elif conditions_length == 1:
        query_filter = conditions[0]

    return query_filter


async def add_split_document_to_collection(
    db_client: AsyncClientAPI,
    documents: List[str],
    file_name: str
) -> None:
    """
    Adds a list of split documents to a specified collection in the ChromaDB.
    This function initializes an embedding function, retrieves or creates a collection
    in the database, and then adds the provided documents to this collection along with
    metadata including the filename, current date, and a predefined user.

    Args:
        db_client (AsyncClientAPI): The asynchronous ChromaDB client used to interact with the database.
        documents (list[str]): A list of document strings to be added to the collection.
        file_name (str): The name of the file associated with the documents.

    Returns:
        dict: A dictionary containing metadata about the added documents, including the filename,
              date, and user.

    """
    embedding_function = initialize_embedding_function()
    collection = None

    try:
        collection = await db_client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME, embedding_function=embedding_function
        )
    except Exception as e:
        print("Failed to get or create collection:", e)
        raise

    m_filename = file_name
    m_date = str(date.today())
    m_user = DEV_USER

    await collection.add(
        ids=[f"{uuid.uuid4()}" for _ in range(len(documents))],
        metadatas=[
            {"filename": m_filename, "date": m_date, "user": m_user}
            for _ in range(len(documents))
        ],
        documents=documents,
    )

    return {"filename": m_filename, "date": m_date, "user": m_user}
