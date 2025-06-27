from typing import Annotated

from fastapi import APIRouter, Body, Depends
from chromadb.api import AsyncClientAPI

from app.database import get_chromadb_client
from app.routers.schemas import Chunks
from app.services.webscraper.get_chunks_service import get_chunks

router = APIRouter()

@router.post(
    "/webscraper/get_chunks",
    response_model=Chunks
)
async def webscraper(
    db_client: Annotated[AsyncClientAPI, Depends(get_chromadb_client)],
    url: str = Body(..., embed=True)
) -> Chunks:
    """
    Endpoint to retrieve content chunks associated with a given URL from the "webscraper" 
    collection in ChromaDB.

    - The endpoint accepts a URL and uses the `get_chunks` service to fetch all chunks 
    (documents and their metadata) linked to the provided URL.
    - Returns the results as a `Chunks` object.

    Workflow:
    1. The endpoint depends on a ChromaDB client (`db_client`), injected using FastAPI's `Depends`.
    2. The client interacts with ChromaDB to retrieve the "webscraper" collection and search 
    for chunks by the provided URL.
    3. The chunks, including their documents and metadata, are returned in the response.
    """
    return await get_chunks(chroma_client=db_client, url=url)
