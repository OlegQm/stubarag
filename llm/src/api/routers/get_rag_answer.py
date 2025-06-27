from typing import List, Dict, Optional

from fastapi import APIRouter, Query, Body

from src.api.services.get_rag_answer_service import send_query
from src.api.routers.schemas import RagResponse

router = APIRouter()

@router.post(
    "/get_rag_answer",
    response_model=RagResponse
)
async def get_rag_answer(
    conversation_content: List[Dict] = Body(
        ...,
        description="Conversation content"
    ),
    needs_enhancement: Optional[bool] = Query(
        True,
        description="True - the question is forwarded to the bot"
    )
) -> RagResponse:
    """
    Endpoint to get an answer from the RAG bot.

    This endpoint receives a list of conversation content in the form of dictionaries
    and returns a response from the RAG bot.
    For example: {"role": "user", "content": "Kto je dekan?"}

    Args:
        conversation_content (List[Dict]):
            A list of dictionaries containing the conversation content.
        needs_enhancement (bool):
            A flag indicating whether the user's query requires enhancement before processing.
            If True, the query is first passed to an enhancement module to refine it,
            improving clarity, adding missing context, or restructuring the request 
            for better results.

    Returns:
        RagResponse: The response from the RAG bot.
    """
    return await send_query(
        conversation_content=conversation_content,
        needs_enhancement=needs_enhancement
    )
