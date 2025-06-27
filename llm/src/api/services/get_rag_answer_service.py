from typing import List, Dict
from json import JSONDecodeError

from src.utils.rag_flow import invoker
from src.api.routers.schemas import RagResponse
from common.logging.global_logger import logger

async def send_query(
    conversation_content: List[Dict],
    needs_enhancement: bool
) -> RagResponse:
    """
    Service to get an answer from the RAG bot.

    This endpoint receives a list of conversation content in the form of dictionaries
    and returns a response from the RAG bot.
    For example: {"role": "user", "content": "Who is the dean?"}

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
    logger.debug("Discord LLM: Processing user query...")
    try:
        result = await invoker(
            conversation_content,
            memory=None,
            needs_enhancement=needs_enhancement
        )
        return RagResponse(answer=result)
    except JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return RagResponse(
            answer="JSON decoding error. Please check the input data."
        )
    except IndexError as e:
        logger.error(f"Index error: {e}")
        return RagResponse(
            answer="Indexing error. Please check the format of the input data."
        )
    except AttributeError as e:
        logger.error(f"Attribute error: {e}")
        return RagResponse(
            answer="Missing expected attribute in the data. "
            "Please check the input data."
        )
    except TimeoutError as e:
        logger.error(f"Timeout error: {e}")
        return RagResponse(
            answer="Request timeout. Please try again later."
        )
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return RagResponse(
            answer="Value error in the input data. "
            "Please check the correctness of the data."
        )
    except Exception as e:
        logger.error(f"Invoker error: {e}")
        return RagResponse(
            answer="An internal error occurred. "
            "Please try again later."
        )
