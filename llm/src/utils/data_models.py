from pydantic import BaseModel, Field
from typing import Annotated, List
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

"""

A module for llm flow's data models.

"""


class RetrieverResponse(BaseModel):
    """
    A model representing the response from a retriever, containing the retrieved context.
    Attributes:
        retrieved_context (str): The context or information retrieved by the retriever.
    """
    retrieved_context: str


class RelevanceCheckerResponse(BaseModel):
    """
    RelevanceCheckerResponse is a model that represents the response from a relevance checker agent.

    Attributes:
        found_relevance (bool): Indicates whether relevance was found (True or False).
    """
    found_relevance: bool = Field(
        ..., description="Indicates whether relevance was found (True or False).")


class UserPromptEnhancerResponse(BaseModel):
    """
    UserPromptEnhancerResponse is a model that represents the response of an user prompt enhancer agent.

    Attributes:
        enhanced_input (str): Enhanced user input.
    """
    enhanced_input: str = Field(..., description="Enhanced user input")


class RagResponse(BaseModel):
    """
    RagResponse is a model that represents the response from a retrieval-augmented generation (RAG) system.

    Attributes:
        answer (str): Answer to the user's query.
        sources (List[str]): List of sources used to generate the answer.
    """
    answer: str = Field(..., description="Answer to the user's query")
    sources: List[str] = Field(
        default_factory=list, description="List of sources used to generate the answer")
    

class PreprocessedContext(BaseModel):
    """
    PreprocessedContext is a data model that represents a structured summary of a context.

    Attributes:
        topic (str): A 2-to-4-sentence abstract summarizing the entire context.
        key_points (List[str]): List of bullet points representing individual ideas or facts.
        details_by_source (str): A collection of distinct facts, with one fact per line.
        glossary (str): A glossary containing abbreviations and their one-line definitions in the format "<abbr.>: <definition>".
    """
    topic: str = Field(..., description="2-to-4-sentence abstract of the entire context")
    key_points: List[str] = Field(
        ..., description="List of single ideas or facts as bullet points")
    details_by_source: List[str] = Field(
        ..., description="List of distinct facts, one fact per line")
    glossary: dict = Field(
        ..., description="Dictionary with abbreviations as keys and their one-line definitions as values")


def control_flow_reducer(left: bool, right: bool) -> bool:
    """
    Merges boolean state variables which controls graph execution
    when graph runs in parallel.

    Args:
        left (bool): The state variable of left node.
        right (bool): The state variable of right node.

    Returns:
        bool: The value of the right argument, indicating if an enhancement is needed.
    """
    return right


def final_answer_reducer(left: RagResponse, right: RagResponse) -> RagResponse:
    """
    Merges `final_answer` state variable when graph runs in parallel.

    Args:
        left (RagResponse): The state variable `final_answer` of left node.
        right (RagResponse): The state variable `final_answer` of right node.

    Returns:
        RagResponse: The value of the right argument, indicating if an enhancement is needed.
    """
    return right


def retriever_response_flow_reducer(left: List[RetrieverResponse], right: List[RetrieverResponse]) -> List[RetrieverResponse]:
    """
    Merges state variable `context` of two nodes.

    Args:
        left (List[RetrieverResponse]): The state variable `context` of left node.
        right (List[RetrieverResponse]): The state variable `context` of right node.

    Returns:
        List[RetrieverResponse]: A merged list containing elements from both input nodes.
    """
    return left + right


def context_preprocessor_flow_reducer(left: PreprocessedContext, right: PreprocessedContext) -> PreprocessedContext:
    """
    Reduces two `PreprocessedContext` objects by selecting the `right` object.
    This function is typically used in scenarios where a sequence of 
    `PreprocessedContext` objects needs to be reduced to a single object, 
    and the reduction logic is to always select the `right` object.
    Args:
        left (PreprocessedContext): The first `PreprocessedContext` object.
        right (PreprocessedContext): The second `PreprocessedContext` object.
    Returns:
        PreprocessedContext: The `right` `PreprocessedContext` object.
    """
    return right


# This defines the object that is passed between each node
# in the graph.
class AgentState(TypedDict):
    """
    AgentState is a TypedDict that represents the state of a llm flow. 
    It includes the following fields:

    Attributes:
        messages (Annotated[List[AnyMessage], add_messages]): 
            A list of messages of the flow, annotated with a function 
            for adding messages.

        context (Annotated[List[RetrieverResponse], retriever_response_flow_reducer]): 
            A list of retriever responses that provide context for the agent, 
            annotated with a function or metadata for reducing the retriever response flow.

        is_relevant (Annotated[bool, control_flow_reducer]): 
            A boolean indicating whether the user's query is relevant, 
            annotated with a function for flow reduction.

        context_available (Annotated[bool, control_flow_reducer]): 
            A boolean indicating whether context is available, annotated with a 
            function for controlling flow reduction.

        final_answer (Annotated[RagResponse, control_flow_reducer]): 
            The final response or answer generated by the agent, annotated with a 
            function for final answer reduction.

        needs_enhancement (Annotated[bool, control_flow_reducer]): 
            A boolean indicating whether the agent's response or state needs 
            further enhancement, annotated with a function or metadata for controlling flow reduction.
    """
    messages: Annotated[List[AnyMessage], add_messages]
    context: Annotated[List[RetrieverResponse],
                       retriever_response_flow_reducer]
    preprocessed_context: Annotated[PreprocessedContext, context_preprocessor_flow_reducer]
    is_relevant: Annotated[bool, control_flow_reducer]
    final_answer: Annotated[RagResponse, final_answer_reducer]
    needs_enhancement: Annotated[bool, control_flow_reducer]
