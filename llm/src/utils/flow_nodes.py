from asyncio import run as arun
from langchain_core.messages import HumanMessage

from src.utils.backend_connection import post_query_lightrag
from src.utils.data_models import RetrieverResponse, RagResponse
from src.utils.llm_utils import get_openai_representation_of_role, initialize_llm_client
from src.utils.llm_agents import (
    spawn_rag_agent,
    spawn_user_prompt_enhancer,
    spawn_relevance_checker,
    spawn_webscrapes_engineer,
    spawn_context_preprocessor
)
from common.logging.global_logger import logger

"""

A module for llm flow's stateful graph nodes.

"""

# DEFINE LLM CLIENTS for graph

main_llm = initialize_llm_client(
    "gpt-4.1-mini",
    streaming=False,
    temperature=0.3,
    top_p=0.9
)
creative_llm = initialize_llm_client(
    "gpt-4.1-nano",
    streaming=False,
    temperature=0.7,
    top_p=1
)
context_llm = initialize_llm_client(
    "gpt-4.1-nano",
    streaming=False,
    temperature=0.4,
    top_p=1
)
grading_llm = initialize_llm_client(
    "gpt-4.1-nano",
    streaming=False,
    temperature=0,
    top_p=0.8
)


def agent_node(state: dict, agent: callable, name: str) -> dict:
    """
    Invokes the given agent with the provided state and processes the result.

    Parameters:
        - state (Any): The current state to be passed to the agent.
        - agent (Agent): The agent to be invoked.
        - name (str): The name to be assigned to the resulting message.

    Returns:
        - dict: A dictionary containing the processed message and the sender's name - the graph state.

    """

    result = agent.invoke(state)
    append_to_messages = False
    append_final_answer = False

    if name == "user_prompt_enhancer":
        result = HumanMessage(
            content=result.enhanced_input,
            additional_kwargs={"name": "user_prompt_enhancer"}
        )
        append_to_messages = True

    if name == "relevance_checker":
        is_relevant = result.found_relevance
        if is_relevant == False:
            result = RagResponse(answer="Vašu požiadavku som vyhodnotil ako irelevantnú k môjmu účelu.", sources=[])
            append_final_answer = True
    else:
        is_relevant = state["is_relevant"]

    if name == "rag":
        append_final_answer = True

    if name == "webscrapes_engineer":
        append_to_messages = True

    return {
        "messages": [result] if append_to_messages == True else state["messages"],
        "context": [],
        "preprocessed_context": result if name == "context_preprocessor" else state["preprocessed_context"],
        "is_relevant": is_relevant,
        "final_answer": result if append_final_answer == True else state["final_answer"],
        "needs_enhancement": False if name == "user_prompt_enhancer" else state["needs_enhancement"],
    }


def rag_node(state):
    """
    Creates a RAG (Retrieval-Augmented Generation) node by spawning a RAG agent 
    and associating it with the given state.

    Args:
        - state: The state object to be passed to the RAG agent and node.

    Returns:
        An agent node configured with the RAG agent and the provided state.
    """
    return agent_node(state=state,
                      agent=spawn_rag_agent(main_llm, state=state), name="rag"
                      )


def context_preprocessor_node(state):
    """
    Creates and returns a context preprocessor node by spawning a context preprocessor agent.
    This function initializes a context preprocessor agent using the `spawn_context_preprocessor` 
    function with the provided `creative_llm` and `state`. 

    Args:
        - state (dict): The current state object to be passed to the context preprocessor agent.
    Returns:
        An agent node configured with the context preprocessor agent and the given state.
    """
    return agent_node(state=state,
                      agent=spawn_context_preprocessor(context_llm, state=state), name="context_preprocessor"
                      )


def user_prompt_enhancer_node(state):
    """
    Creates an user prompt enhancer node by spawning a User prompt
    enhancment agent and associating it with the given state.

    Args:
        - state (dict): The current state or context to be passed to the 
                      agent and node.

    Returns:
        Node: A configured agent node named "user_prompt_enhancer" 
              that enhances user prompts.
    """
    return agent_node(state=state,
                      agent=spawn_user_prompt_enhancer(creative_llm, state=state), name="user_prompt_enhancer"
                      )


def relevance_checker_node(state):
    """
    Creates a relevance checker node by spawning a Relevance
    checker agent and associating it with the given state.

    Args:
        - state (dict): The current state or context to be passed to the 
                      agent and node.
    Returns:
        Node: A configured agent node named "relevance_checker" 
              that checks the relevance of the user's query.
    """
    return agent_node(state=state, agent=spawn_relevance_checker(grading_llm, state=state), name="relevance_checker"
                      )


def webscrapes_engineer_node(state):
    """
    Creates a webscrapes engineer node by spawning a Webscrapes
    engineer agent and associating it with the given state.
    Args:
        - state (dict): The current state or context to be passed to the 
                    agent and node.
    Returns:
        Node: A configured agent node named "webscrapes_engineer" 
            that generates webscrapes for the user's query.
    """
    return agent_node(state=state,
                      agent=spawn_webscrapes_engineer(creative_llm, state=state), name="webscrapes_engineer"
                      )


def lightrag_node(state: dict):
    """
    Processes the given state dictionary to interact with the Lightrag system and 
    retrieve relevant context for a conversation.

    Args:
        state (dict): A dictionary containing the current state of the conversation. 
                      Expected keys include:
                      - "messages": A list of message objects, where each message has 
                        attributes like `type` (e.g., "human", "ai") and `content`.
                      - "is_relevant": A boolean indicating if the current state is relevant.
                      - "context_available": A boolean indicating if context is available.
                      - "final_answer": The final answer for the conversation.

    Returns:
        dict: A dictionary containing the updated state with the following keys:
              - "messages": The original list of messages from the input state.
              - "context": A list containing a `RetrieverResponse` object with the 
                retrieved context from Lightrag.
              - "is_relevant": The original `is_relevant` value from the input state.
              - "context_available": The original `context_available` value from the input state.
              - "final_answer": The original `final_answer` value from the input state.
              - "needs_enhancement": A boolean set to `False`, indicating no further 
                enhancement is needed.

    Raises:
        Logs an error if querying Lightrag fails and sets the retrieved context to 
        "Failed to query Lightrag." in such cases.
    """

    # Filter out the relevant conversation messages
    conversation_messages = [
        {"role": get_openai_representation_of_role(
            message.type), "content": message.content}
        for message in state["messages"]
        if (message.type == "human"
            or (message.type == "ai" and not message.tool_calls))
        and message.content != ""
    ]

    if conversation_messages:
        query = conversation_messages[-1]["content"]
        conversation_history = conversation_messages[:-1]
    else:
        logger.error("No valid conversation messages found.")
        query = ""
        conversation_history = []
    try:
        lightrag_response = arun(
            post_query_lightrag(query, conversation_history))
    except Exception as e:
        logger.error(f"Failed to query Lightrag: {e}")
        lightrag_response = "Failed to query Lightrag."

    return {
        "messages": state["messages"],
        "context": [RetrieverResponse(retrieved_context=lightrag_response)],
        "preprocessed_context": None,
        "is_relevant": state["is_relevant"],
        "final_answer": state["final_answer"],
        "needs_enhancement": False,
    }
