from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from chromadb.api import AsyncClientAPI

from app.services.faq.load_faq_data_service import load_faq_data
from app.database import get_chromadb_client
from app.routers.schemas import LoadFaqDataResponse

router = APIRouter()

@router.post(
    "/faq/load_records",
    response_model=LoadFaqDataResponse
)
async def load_data(
    data: List[Dict[str, Any]],
    db_client: AsyncClientAPI = Depends(get_chromadb_client)
) -> LoadFaqDataResponse:
    """
        Loads data into the FAQ collection in Chroma DB.

        This endpoint allows uploading a list of questions and answers into the FAQ collection
        within Chroma DB. The data should include the question text, the answer, and optional
        fields such as document name and URL.

        Args:
            data (List[Dict[str, Any]]): A list of dictionaries where each dictionary represents a question and answer pair. 
                Example format:
                [
                    {
                        "question": "What is FastAPI?",
                        "answer": "FastAPI is a modern web framework for Python.",
                        "doc": "FastAPI Documentation",
                        "url": "http://fastapi.tiangolo.com/"
                    }
                ]
            db_client (AsyncClientAPI): The Chroma database client instance used to interact with the collection.

        Returns:
            JSON response with a success message if the data is loaded successfully.
    """

    return await load_faq_data(data=data, db_client=db_client)
