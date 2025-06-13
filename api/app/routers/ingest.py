from typing import Annotated

from app.routers.schemas import IngestResponse
from app.database import get_chromadb_client
from app.services.ingest_service import (
    file_ingestion,
    text_ingestion,
)
from chromadb.api import AsyncClientAPI
from fastapi import APIRouter, Depends, File, Query, Request, UploadFile, status
from pymongo.collection import Collection

"""

This module defines the API endpoints for data ingestion in the application.

"""

router = APIRouter()


@router.post("/ingest_file", status_code=status.HTTP_201_CREATED)
async def upload_file(
    chroma_client: Annotated[AsyncClientAPI, Depends(get_chromadb_client)],
    file: UploadFile = File(...),
) -> IngestResponse:
    """
    Endpoint to handle file uploads for ingestion.
    This asynchronous function receives a file and a ChromaDB client instance, 
    then processes the file ingestion using the provided client.

    Args:
        chroma_client (AsyncClientAPI): The ChromaDB client instance, injected via dependency.
        file (UploadFile): The file to be uploaded and ingested.

    Returns:
        IngestResponse: The response after processing the file ingestion.

    """

    return await file_ingestion(chroma_client, file)


@router.post("/ingest_text", status_code=status.HTTP_201_CREATED)
async def upload_document(
    chroma_client: Annotated[AsyncClientAPI, Depends(get_chromadb_client)],
    request: Request,
) -> IngestResponse:
    """
    Endpoint to upload a document for ingestion.
    This asynchronous function handles the uploading of a document and processes it using the provided ChromaDB client.

    Args:
        chroma_client (AsyncClientAPI): The ChromaDB client instance, injected via dependency.
        request (Request): The request object containing the document to be ingested.

    Returns:
        IngestResponse: The response after processing the document ingestion.

    """
    return await text_ingestion(chroma_client, request)


# TODO: Implement this endpoint
# @router.get("/ingest_from_db", status_code=status.HTTP_201_CREATED)
# async def upload_document_from_db(
#     chroma_client: Annotated[AsyncClientAPI, Depends(get_chromadb_client)],
#     mongo_client: Annotated[Collection, Depends(get_mongodb_client)],
#     object_id: Annotated[str, Query(..., description="The object id to query")],
# ):
#     return await from_db_ingestion(chroma_client, mongo_client, object_id)
