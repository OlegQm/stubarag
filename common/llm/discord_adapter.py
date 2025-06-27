from httpx import AsyncClient, Timeout

from common.logging.global_logger import logger
from common.session.decorators import http_timer

"""

A module for interconnection between Discord chatbot and LLM agents.

"""


class DiscordAdapter:
    """
    A class to handle the routing of conversation flows in Discord chatbot.

    Methods:

        __init__():
            Initializes the DiscordAdapter instance.
            Builds a state graph for llm for entire session.

        send_query(conversation_content):
            Returns response to provided conversation.
    """
    
    @http_timer
    async def send_query(self, conversation_content: list[dict]) -> str:
        """
        Connect to the "send_query" interface in the frontend app.

        This interface was originally implemented in the frontend app to handle user queries.

        Args:
            - conversation_content (list[dict]): The content of the conversation as a list of dictionaries.
        Returns:
            - str: The response from the appropriate handler.

        """

        logger.debug("Discord LLM: Processing user query...")
        # response = await ainvoker(conversation_content, self.workflow, needs_enhancement=True)

        BASE_URL = "http://llm:8507"

        async with AsyncClient(timeout=Timeout(60.0, connect=10.0)) as client:
            response = await client.post(f"{BASE_URL}/llm/get_rag_answer", json=conversation_content)

        answer = response.json()["answer"]
        logger.debug(answer)
        return answer