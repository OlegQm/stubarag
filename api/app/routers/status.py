from fastapi import APIRouter, Depends
from chromadb import AsyncHttpClient

from app.database import mongo_db, get_chromadb_client

router = APIRouter()

"""

This module defines the status endpoint for the API.

Endpoint:
- `status` endpoint performs the following checks: verifies the connection to 
    MongoDB and ChromaDB.

"""


@router.get("/status",)
async def server_status(chroma_client: AsyncHttpClient = Depends(get_chromadb_client)):
    """
    Check the health status of the server, MongoDB, and ChromaDB.
    This asynchronous function verifies the connection status of MongoDB and ChromaDB,
    and returns a JSON response indicating their health status.

    Args:
        chroma_client (AsyncHttpClient, optional): An asynchronous HTTP client for ChromaDB. 
            Defaults to the client provided by the dependency injection system.

    Returns:
        dict: A dictionary containing the overall server status and the individual 
              statuses of MongoDB and ChromaDB. The possible values for each status 
              are "HEALTHY" or "UNHEALTHY".

    """

    check_mongo = mongo_db.verify_connection()
    check_chroma = chroma_client is not None

    mongo_status = "HEALTHY" if check_mongo else "UNHEALTHY"
    chroma_status = "HEALTHY" if check_chroma else "UNHEALTHY"

    return {"status": "HEALTHY", "mongodb": mongo_status, "chromadb": chroma_status}
