import functools
import json
import os
from typing import Dict
from common.llm.llm_agents import (
    spawn_rag_agent, spawn_user_prompt_enhancer, spawn_relevance_checker, spawn_context_checker)
from common.llm.llm_utils import AgentState, agent_node, initialize_llm_client, process_flow_output
from common.logging.global_logger import logger
from common.session.decorators import callable_timer
from common.llm.llm_utils import build_webscrapes_subgraph, build_documents_mimic_prompt_subgraph, build_documents_keywords_subgraph

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from asyncio import run as arun
from langfuse.callback import CallbackHandler

if os.getenv("ENV") == "localhost":
    # TEMPORARY global langfuse handler for demo purposes of LLM monitoring
    langfuse_handler = CallbackHandler(secret_key="sk-lf-912749f3-9aaa-4a5d-80af-6d2fb52e95ad",
                                       public_key="pk-lf-fd6bb985-53b5-49e6-9478-1c16aa093aa2",
                                       host="http://langfuse-web:8030")

"""

A module for the RAG workflow for the LLM agents.

"""

# DEFINE EDGE LOGIC

def router(state: dict) -> str:
    """
    Routes the flow based on the state of the conversation.

    Args:
        - state (dict): A dictionary containing the current state of the conversation. 
                      Expected keys include:
                      - "messages": A list of message objects, where the last message contains the agent's output in JSON format.
                      - "tools_calls": A list of tool calls made by the agent.
                      - "special_requests": A list of special requests made by the user.

    Returns:
        - str: A string indicating the next step in the flow. Possible values are:
             - "call_tool": If the previous agent is invoking a tool.
             - "IRRELEVANT": If the last agent output indicates no relevance found.
             - "NO CONTEXT": If the last agent output indicates no context available.
             - "user_prompt_enhancer": If there is a special request for prompt enhancement.
             - "continue": To continue with the next agent.
    """
    try:
        last_agent_output = json.loads(state["messages"][-1].content)
        logger.debug(f"Last agent output: {last_agent_output}")
    except Exception as e:
        logger.error(f"Failed to parse last agent output: {e}")
        return "context_checker"

    if state["needs_enhancement"] == True:
        logger.debug("Routing to enhance_prompt...")
        return "user_prompt_enhancer"
    elif ("found_relevance" in last_agent_output and last_agent_output["found_relevance"] == "No"):
        logger.debug("Irrelevant querry -> Routing to END...")
        return END
    elif ("context_available" in last_agent_output and last_agent_output["context_available"] == "No"):
        logger.debug("No available context -> routing to END...")
        return END
    elif ("found_relevance" in last_agent_output and last_agent_output["found_relevance"] == "Yes"):
        logger.debug("Routing to retrievers...")
        return ["documents_keywords_subgraph", "webscrapes_subgraph"]
    elif "enhanced_input" in last_agent_output:
        logger.debug("Using enhanced input -> Routing to retrievers...")
        return ["documents_keywords_subgraph", "webscrapes_subgraph"]
    else:
        # Continue with the next agent
        logger.debug("Continuing to the rag agent...")
        return "rag"


# DEFINE WORKFLOW

@callable_timer
def build_graph(language_models: Dict[str, str] = {'main_llm': 'gpt-4o-mini', 'creative_llm': 'gpt-4o-mini', 'grading_llm': 'gpt-4o-mini'}) -> StateGraph:
    """
    Builds and compiles a state graph for a RAG (Retrieval-Augmented Generation) workflow.

    Args:
        language_models (Dict[str,str]): A dictionary containing the language models to be used in the workflow.

    Returns:
        StateGraph: The compiled state graph representing the RAG workflow.

    The workflow consists of the following nodes:
        - embeddings_engineer: Node responsible for embedding engineering.
        - rag: Node representing the RAG agent.
        - call_tool: Node for managing all the tools.
        - user_prompt_enhancer: Node for enhancing user prompts.
        - relevance_checker: Node for checking the relevance of the retrieved documents.
        - context_checker: Node for checking the context of the conversation.

    The workflow includes conditional edges to determine the flow between nodes based on specific conditions:
        - From relevance_checker to either user_prompt_enhancer, embeddings_engineer, or END based on router.
        - From user_prompt_enhancer to embeddings_engineer based on router.
        - From embeddings_engineer to either context_checker or call_tool based on router.
        - From context_checker to either rag or END based on router.
        - From call_tool back to context_checker based on the sender field.

    The graph is compiled with the memory checkpointer.
    """
    ### DEFINE LLM CLIENTS for graph ###

    # LLM with streaming enabled for communication with the user.
    main_llm = initialize_llm_client(
        language_models["main_llm"], streaming=False, temperature=0.4, top_p=0.8
    )
    # LLM with streaming disabled for creative tasks.
    creative_llm = initialize_llm_client(
        language_models["creative_llm"], streaming=False, temperature=0.7, top_p=1)
    # LLM with streaming disabled for grading and evaluating tasks.
    grading_llm = initialize_llm_client(
        language_models["grading_llm"], streaming=False, temperature=0, top_p=0.8)

    ### DEFINE NODES ###


    rag_node = functools.partial(
        agent_node, agent=spawn_rag_agent(main_llm), name="rag")
    user_prompt_enhancer_node = functools.partial(
        agent_node, agent=spawn_user_prompt_enhancer(creative_llm), name="user_prompt_enhancer"
    )
    relevance_checker_node = functools.partial(
        agent_node, agent=spawn_relevance_checker(grading_llm), name="relevance_checker"
    )
    context_checker_node = functools.partial(
        agent_node, agent=spawn_context_checker(grading_llm), name="context_checker"
    )
    logger.debug("Agent nodes successfully created.")


    #documents_mimic_subgraph = build_documents_mimic_prompt_subgraph(creative_llm)
    documents_keywords_subgraph = build_documents_keywords_subgraph(creative_llm) 
    webscrapes_subgraph = build_webscrapes_subgraph(creative_llm)


    ### DEFINE WORKFLOW ###

    workflow = StateGraph(AgentState)

    workflow.add_node("rag", rag_node)
    workflow.add_node("user_prompt_enhancer", user_prompt_enhancer_node)
    workflow.add_node("relevance_checker", relevance_checker_node)
    workflow.add_node("context_checker", context_checker_node)
    #workflow.add_node("documents_mimic_subgraph", documents_mimic_subgraph)
    workflow.add_node("documents_keywords_subgraph", documents_keywords_subgraph)
    workflow.add_node("webscrapes_subgraph", webscrapes_subgraph)
    
    logger.debug("Nodes successfully added to the workflow.")

    workflow.set_entry_point("relevance_checker")

    workflow.add_conditional_edges("relevance_checker", router)

    workflow.add_conditional_edges("user_prompt_enhancer", router)

    workflow.add_edge(["documents_keywords_subgraph", "webscrapes_subgraph"], "context_checker")

    workflow.add_conditional_edges("context_checker", router)

    workflow.set_finish_point("rag")

    logger.debug("Edges successfully added to the workflow.")

    return workflow


# INVOKER

def invoker(conversation_content: list[dict], memory: MemorySaver = None, workflow: StateGraph = None, needs_enhancement: bool = False) -> str:
    """
    Invokes a language model workflow with the given conversation content, memory, and special requests.

    Args:
        - conversation_content (list[dict]): A list of dictionaries containing the conversation messages.
        - memory (MemorySaver, optional): An instance of MemorySaver for checkpointing the workflow. Defaults to None.
        - workflow (StateGraph, optional): An instance of StateGraph representing the workflow to be executed. Defaults to None.
        - special_requests (list[str], optional): A list of special requests to be considered during the workflow execution. Defaults to an empty list.

    Returns:
        - str: Serialized RagResponse object.
    """
    # Build the graph using the provided memory checkpointer
    graph = workflow.compile(checkpointer=memory)

    # Invoke the graph with the conversation content, special requests and configuration
    try:
        logger.debug("Invoking a LLM...")
        events = arun(graph.ainvoke(
            input={
                "messages": conversation_content,
                "needs_enhancement": needs_enhancement,
            },
            config={"configurable": {"thread_id": 1},
                    "recursion_limit": 100, "callbacks": ([langfuse_handler] if os.getenv("ENV") == "localhost" else [])},
        ))
        logger.debug("Successfully invoked a LLM.")

    except Exception as e:
        logger.error(f"Failed to invoke a LLM: {e}")

    # Extract the response from the last message in the events
    try:
        rag_response = process_flow_output(events)
        logger.debug("Succesfully parsed a LLM answer.")

    except Exception as e:
        logger.error(f"Failed to generate an answer: {e}")
        rag_response = "Failed to generate an answer. Please try again later."

    logger.debug("Workflow execution completed.")

    # Return the generated response
    return rag_response


async def ainvoker(conversation_content: list[dict], workflow: StateGraph = None, needs_enhancement: bool = False) -> str:
    """
    Invokes a graph-based workflow to process a conversation and generate a LLM response (used by Discord).
    Compared to sync invoker, ainvoker doesn't hold graph state in memory and doesn't call asyncio.run()

    Args:
        - conversation_content (list[dict]): A list of dictionaries representing the conversation messages.
        - workflow (StateGraph): The compiled state graph representing the RAG workflow.
        - special_requests (list[str]): List of strings representing aditional requests for AI Agents.
    Returns:
        - str: Serialized RagResponse object.

    Raises:
        - Exception: If there is an error during the workflow execution, returns a default failure message.

    """
    # Build the graph using the provided memory checkpointer
    graph = workflow.compile()

    # Invoke the graph with the conversation content, special requests and configuration
    try:
        logger.debug("Invoking a LLM...")
        events = await graph.ainvoke(
            input={
                "messages": conversation_content,
                "needs_enhancement": needs_enhancement,
            },
            config={"configurable": {"thread_id": 1},
                    "recursion_limit": 100, "callbacks": ([langfuse_handler] if os.getenv("ENV") == "localhost" else [])},
        )
        logger.debug("Successfully invoked a LLM.")

    except Exception as e:
        logger.error(f"Failed to invoke a LLM: {e}")

    # Extract the response from the last message in the events
    try:
        rag_response = process_flow_output(events)
        logger.debug("Succesfully parsed a LLM answer.")

    except Exception as e:
        logger.error(f"Failed to generate an answer: {e}")
        rag_response = "Failed to generate an answer. Please try again later."

    logger.debug("Workflow execution completed.")

    # Return the generated response
    return rag_response
