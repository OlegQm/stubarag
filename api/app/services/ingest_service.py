from tempfile import NamedTemporaryFile
from bson import ObjectId
import pymupdf4llm

from app.routers.schemas import IngestResponse
from app.utils import add_split_document_to_collection, text_splitter
from chromadb.api import AsyncClientAPI
from fastapi import HTTPException, Request, UploadFile, status
from langchain_community.document_loaders import JSONLoader
from langchain_text_splitters import MarkdownTextSplitter
from pymongo.collection import Collection

"""

This module provides services for ingesting various types of files and text into ChromaDB database.
It includes functions for handling file uploads, processing text data, and interacting with a ChromaDB collection.

Functions:
- file_ingestion: Handles the ingestion of PDF and JSON files, processes the content, and stores metadata in the chromadb.
- text_ingestion: Handles the ingestion of plain text or JSON text data, processes the content, and stores metadata in the chromadb.
- from_db_ingestion: (TODO) Retrieves and processes data from a MongoDB collection based on an ObjectId.

"""


async def file_ingestion(db_client: AsyncClientAPI, file: UploadFile):
    """
    Asynchronously handles the ingestion of a file into the system.
    This function processes files of type PDF and JSON, validates their content type,
    reads the file content, and processes it accordingly. The processed content is then
    added to a chromadb collection.

    Args:
        db_client (AsyncClientAPI): The asynchronous chromadb client used for storing the processed documents.
        file (UploadFile): The file to be ingested, which should be of type PDF or JSON.

    Raises:
        HTTPException: If the file content type is not supported (415 Unsupported Media Type).
        HTTPException: If there is an error during file processing (500 Internal Server Error).

    Returns:
        IngestResponse: A response object containing a success message and metadata about the ingested file.

    """

    allowed_content_types = [
        "application/pdf",
        "application/json",
    ]

    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Invalid content type",
        )

    try:
        file_content = await file.read()
        file_name = file.filename
        metadatas = {}

        if file.content_type == "application/json":
            suffix = ".json"
        else:
            suffix = ".pdf"

        with NamedTemporaryFile(suffix=suffix) as temp_file:
            temp_file.write(file_content)
            temp_file.seek(0)

            if file.content_type == "application/pdf":
                md_text = pymupdf4llm.to_markdown(temp_file.name)
                splitter = MarkdownTextSplitter(
                    chunk_size=900, chunk_overlap=450)
                docs = splitter.create_documents([md_text])

            else:
                document_loader = JSONLoader(temp_file.name)
                docs = document_loader.load_and_split(
                    text_splitter=text_splitter)

            documents = [doc.page_content for doc in docs]

            metadatas = await add_split_document_to_collection(
                db_client, documents, file_name
            )

        if file.content_type == "application/pdf":
            return IngestResponse(
                message="PDF processed successfully", metadatas=metadatas
            )
        else:
            return IngestResponse(
                message="JSON processed successfully", metadatas=metadatas
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


async def text_ingestion(db_client: AsyncClientAPI, request: Request):
    """
    Handles the ingestion of text data from a request, processes it, and stores it in the database.

    Args:
        db_client (AsyncClientAPI): The asynchronous database client used to interact with the chromadb.
        request (Request): The incoming request containing the text data to be ingested.

    Raises:
        HTTPException: If the content type is not supported, the JSON format is invalid, or the text field is missing.

    Returns:
        IngestResponse: An object containing a success message and metadata about the ingested text.

    """

    document = None
    file_name = "text"

    if request.headers.get("Content-Type") == "text/plain":
        document = await request.body()
        document = document.decode("utf-8")
    elif request.headers.get("Content-Type") == "application/json":
        try:
            text_request = await request.json()
            document = text_request["text"]
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON format")
    else:
        raise HTTPException(status_code=415, detail="Invalid content type")

    if not document:
        raise HTTPException(status_code=400, detail="Text field is required")

    documents = text_splitter.split_text(document)

    metadatas = await add_split_document_to_collection(db_client, documents, file_name)

    return IngestResponse(message="Text processed successfully", metadatas=metadatas)


# TODO: Implement this function
# async def from_db_ingestion(
#     db_client: AsyncClientAPI, mongo_collection: Collection, object_id: str
# ):

#     object_id = ObjectId(object_id)
#     history_data = mongo_collection.find_one({"_id": object_id})

#     print(history_data, flush=True)

#     # documents = text_splitter.split_text(document)

#     # metadatas = await add_split_document_to_collection(db_client, documents, file_name)

#     return history_data
#     # return IngestResponse(message="Data processed successfully", metadatas=history_data)
