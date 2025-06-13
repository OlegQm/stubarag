from typing import Dict, Any, List
import uuid
import logging

from fastapi import status
from fastapi.responses import JSONResponse
from chromadb.api import AsyncClientAPI

from app.utils import initialize_embedding_function
from app.routers.schemas import LoadFaqDataResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def return_load_data_response(
    message: str,
    status: int
) -> JSONResponse:
    response_data = LoadFaqDataResponse(
        message=message,
        status=status
    )
    return JSONResponse(
        content=response_data.model_dump(),
        status_code=status
    )

async def load_faq_data(
    db_client: AsyncClientAPI,
    data: List[Dict[str, Any]]
) -> JSONResponse:
    """
    Loads a list of FAQ data into the Chroma DB FAQ collection.
    Prevents duplicates by checking existing questions in the metadata.
    """
    if not data:
        return return_load_data_response(
            message="Invalid data format. Expected a non-empty list of dictionaries.",
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        embedding_function = initialize_embedding_function()
        
        collection = await db_client.get_or_create_collection(
            name="faq",
            embedding_function=embedding_function
        )

        existing_data = await collection.get(include=["metadatas"])
        existing_metadatas = existing_data.get("metadatas", [])
        
        existing_questions = {meta.get("question") for meta in existing_metadatas}
        
        max_no = max((meta.get("no", 0) for meta in existing_metadatas), default=0)
        filtered_data = []

        for idx, item in enumerate(data):
            question = item["question"]
            if question in existing_questions:
                logger.info(f"Duplicate found. Skipping question: {question}")
                continue
            filtered_data.append({
                "id": str(uuid.uuid4()),
                "metadata": {
                    "no": max_no + idx + 1,
                    "doc": item.get("doc", "default_doc"),
                    "url": item.get("url", "http://example.com"),
                    "question": question,
                    "answer": item["answer"]
                }
            })

        if not filtered_data:
            return return_load_data_response(
                message="No new data to load. All entries are duplicates.",
                status=status.HTTP_201_CREATED
            )

        ids = [entry["id"] for entry in filtered_data]
        metadatas = [entry["metadata"] for entry in filtered_data]
        documents = [entry["metadata"]["question"] for entry in filtered_data]

        await collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        return return_load_data_response(
            message=f"Successfully loaded {len(filtered_data)} unique entries.",
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        return return_load_data_response(
            message=f"Error loading data: {str(e)}",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )