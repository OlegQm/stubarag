import os

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode
from langfuse.callback import CallbackHandler

from src.utils.flow_nodes import (
    rag_node,
    user_prompt_enhancer_node,
    relevance_checker_node,
    lightrag_node,
    webscrapes_engineer_node,
    context_preprocessor_node
)
from src.utils.llm_utils import process_flow_output

from src.utils.data_models import AgentState
from common.logging.global_logger import logger
from common.session.decorators import callable_timer
from src.utils.agent_tools import webscrapes_retriever

if os.getenv("ENV") == "localhost":
    # TEMPORARY global langfuse handler for demo purposes of LLM monitoring
    langfuse_handler = CallbackHandler(
        secret_key="sk-lf-912749f3-9aaa-4a5d-80af-6d2fb52e95ad",
        public_key="pk-lf-fd6bb985-53b5-49e6-9478-1c16aa093aa2",
        host="http://langfuse-web:8030"
    )

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

    if state["needs_enhancement"] == True:
        logger.debug("Routing to enhance_prompt...")
        return "user_prompt_enhancer"
    elif state["is_relevant"] == False:
        logger.debug("Irrelevant query -> Routing to END...")
        return END
    elif state["is_relevant"] == True and state["context"] == []:
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
    Constructs and returns a StateGraph object representing the workflow for a 
    retrieval-augmented generation (RAG) process.
    The workflow consists of multiple nodes and edges that define the flow of 
    operations, including relevance checking, user prompt enhancement, context 
    checking, and integration of knowledge from various sources such as 
    LightRAG and web scrapes.
    Nodes:
        - "rag": Final node representing the RAG process.
        - "user_prompt_enhancer": Enhances the user prompt for better context.
        - "relevance_checker": Checks the relevance of the input or context.
        - "context_checker": Validates the context for completeness and accuracy.
        - "lightrag_knowledge": Integrates knowledge from LightRAG.
        - "webscrapes_subgraph": Subgraph handling web scraping operations.
    Edges:
        - Conditional edges are added based on a router function to determine 
          the flow between nodes.
        - Direct edges connect specific nodes, such as from "lightrag_knowledge" 
          and "webscrapes_subgraph" to "context_checker".
    Entry and Exit Points:
        - Entry point: "relevance_checker"
        - Finish point: "rag"
    Returns:
        StateGraph: The constructed workflow graph with nodes and edges defined.
    """

    webscrapes_subgraph = build_webscrapes_subgraph()

    workflow = StateGraph(AgentState)

    workflow.add_node("rag", rag_node)
    workflow.add_node("user_prompt_enhancer", user_prompt_enhancer_node)
    workflow.add_node("relevance_checker", relevance_checker_node)
    workflow.add_node("context_preprocessor", context_preprocessor_node)
    workflow.add_node("lightrag_knowledge", lightrag_node)
    workflow.add_node("webscrapes_subgraph", webscrapes_subgraph)

    logger.debug("Nodes successfully added to the workflow.")

    workflow.set_entry_point("relevance_checker")
    workflow.add_conditional_edges("relevance_checker", router)
    workflow.add_conditional_edges("user_prompt_enhancer", router)
    workflow.add_edge(
        [
            "lightrag_knowledge",
            "webscrapes_subgraph"
        ],
        "context_preprocessor"
    )
    workflow.add_edge("context_preprocessor", "rag")
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
                "preprocessed_context": None,
                "final_answer": None,
                "needs_enhancement": needs_enhancement,
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
