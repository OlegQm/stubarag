import os

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

from src.utils.flow_nodes import (
    rag_node,
    relevance_checker_node,
    lightrag_node,
    webscrapes_engineer_node
)
from src.utils.llm_utils import process_flow_output

from src.utils.data_models import AgentState
from common.logging.global_logger import logger
from common.session.decorators import callable_timer
from src.utils.agent_tools import webscrapes_retriever

# Initialise Langfuse once at start‑up when developing locally.
# In production, prefer environment variables over the constructor args below.
if os.getenv("ENV") == "localhost":
    # These values can also come from the environment – we fall back to a public demo key
    Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),  # Optional if you only need read‑only traces
        host="http://langfuse-web:8030",
    )
    # Create the LangChain ↔ Langfuse bridge.  No constructor args are supported in v3.
    langfuse_handler = CallbackHandler()

"""
A module for the RAG workflow for the LLM agents.
"""


# DEFINE EDGE LOGIC

def router(state: dict) -> str:
    """
    Determines the next step in the RAG (Retrieval-Augmented Generation) flow 
    based on the provided state dictionary.
    Args:
        state (dict): A dictionary containing the current state with the following keys:
            - "needs_enhancement" (bool): Indicates if the user prompt needs enhancement.
            - "is_relevant" (bool): Specifies whether the query is relevant.
            - "context_available" (bool): Indicates if context is available.
            - "context" (list): A list representing the available context.
    Returns:
        str or list: The next step in the flow. Possible return values:
            - "user_prompt_enhancer": If the prompt needs enhancement.
            - END: If the query is irrelevant or no context is available.
            - ["lightrag_knowledge", "webscrapes_subgraph"]: If the query is relevant but no context is provided.
            - "rag": If the query is relevant and context is available.
    """

    if not state["is_relevant"]:
        logger.debug("Irrelevant query -> Routing to END...")
        return END
    elif state["is_relevant"] and not state["context"]:
        logger.debug("Routing to retrievers...")
        return ["lightrag_knowledge", "webscrapes_subgraph"]
    else:
        logger.debug("Continuing to the rag agent...")
        return "rag"


# DEFINE WORKFLOW

def build_webscrapes_subgraph() -> str:
    """
    Constructs and compiles a state graph subgraph for a web scraping workflow.
    This function creates a subgraph that consists of nodes and edges representing
    the flow of states in a web scraping process. It initializes the required tools,
    defines the nodes for the subgraph, and establishes the transitions between them.
    Finally, the subgraph is compiled and returned.

    Returns:
        str: The compiled state graph subgraph for the web scraping workflow.
    """

    tools = [webscrapes_retriever]

    python_runner = ToolNode(tools)

    subgraph = StateGraph(AgentState)

    subgraph.add_node("webscrapes_engineer", webscrapes_engineer_node)
    subgraph.add_node("python_runner", python_runner)

    subgraph.add_edge(START, "webscrapes_engineer")
    subgraph.add_edge("webscrapes_engineer", "python_runner")
    subgraph.add_edge("python_runner", END)

    subgraph = subgraph.compile()

    return subgraph


@callable_timer
def build_graph() -> StateGraph:
    """
    Build and configure a StateGraph workflow for RAG (Retrieval-Augmented Generation) processing.
    
    This function creates a workflow graph that orchestrates the flow between different nodes
    for document retrieval and generation. The workflow includes relevance checking,
    knowledge retrieval from LightRAG, web scraping capabilities, and final RAG processing.
    
    The workflow structure:
    1. Entry point: relevance_checker - validates input relevance
    2. Conditional routing based on relevance check results
    3. Parallel processing through lightrag_knowledge and webscrapes_subgraph nodes
    4. Final processing through rag node
    5. Exit point: rag - generates final response
    
    Returns:
        StateGraph: A configured workflow graph with all nodes, edges, and routing logic
                   set up for RAG processing pipeline.
    
    Raises:
        Any exceptions from underlying node creation or graph configuration operations.
    """

    webscrapes_subgraph = build_webscrapes_subgraph()

    workflow = StateGraph(AgentState)

    workflow.add_node("rag", rag_node)
    workflow.add_node("relevance_checker", relevance_checker_node)
    workflow.add_node("lightrag_knowledge", lightrag_node)
    workflow.add_node("webscrapes_subgraph", webscrapes_subgraph)

    logger.debug("Nodes successfully added to the workflow.")

    workflow.set_entry_point("relevance_checker")
    workflow.add_conditional_edges("relevance_checker", router)
    workflow.add_edge(
        [
            "lightrag_knowledge",
            "webscrapes_subgraph"
        ],
        "rag"
    )
    workflow.set_finish_point("rag")

    logger.debug("Edges successfully added to the workflow.")

    return workflow


# INVOKER

async def invoker(
    conversation_content: list[dict],
    memory: MemorySaver = None,
    needs_enhancement: bool = False
) -> str:
    """
    Invokes a language model workflow with the given conversation content,
        memory, and special requests.

    Args:
        conversation_content (list[dict]):
            A list of dictionaries containing the conversation messages.
        memory (MemorySaver, optional):
            An instance of MemorySaver for checkpointing the workflow.
            Defaults to None.
        needs_enhancement (bool, optional):
            Flag indicating if prompt enhancement is needed.
            Defaults to False.

    Returns:
        str: Serialized RagResponse object.
    """

    try:
        workflow = build_graph()
    except Exception as e:
        logger.error(f"Failed to build the graph: {e}")

    # Build the graph using the provided memory checkpointer
    graph = workflow.compile(checkpointer=memory)

    # Invoke the graph with the conversation content and configuration
    try:
        logger.debug("Invoking a LLM...")
        events = await graph.ainvoke(
            input={
                "messages": conversation_content,
                "context": [],
                "is_relevant": True,
                "final_answer": None
            },
            config={
                "configurable": {"thread_id": 1},
                "recursion_limit": 100,
                "callbacks": (
                    [langfuse_handler] if os.getenv("ENV") == "localhost"
                    else []
                )
            },
        )
        logger.debug("Successfully invoked a LLM.")
    except Exception as e:
        logger.error(f"Failed to invoke a LLM: {e}")
        return "Failed to invoke a LLM."

    # Extract the response from the last message in the events
    try:
        rag_response = process_flow_output(events["final_answer"])
        logger.debug("Successfully parsed a LLM answer.")
    except Exception as e:
        logger.error(f"Failed to generate an answer: {e}")
        rag_response = "Failed to generate an answer. Please try again later."

    logger.debug("Workflow execution completed.")

    return rag_response
