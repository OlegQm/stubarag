from pydantic import BaseModel

class RagResponse(BaseModel):
    """
    RagResponse is a model designed to receive a response from the RAG bot.
    Attributes:
        answer (str): The response provided by the RAG bot.
    """

    answer: str
