import operator
import os
import json
import functools
from typing import Annotated, Sequence

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict
from asyncio import run as arun

from common.llm.backend_connection import get_retrieve_data
from common.llm.agent_tools import documents_retriever_keywords_prompt, documents_retriever_mimic_prompt, webscrapes_retriever
from common.llm.llm_agents import spawn_keywords_documents_engineer, spawn_mimic_documents_engineer, spawn_webscrapes_engineer
from common.logging.global_logger import logger

"""

A module for utility functions used by chat workflow.

"""

# This defines the object that is passed between each node
# in the graph. We will create different nodes for each agent and tool


def needs_enhancement_reducer(left: bool, right: bool) -> bool:
    """
    Merges state value "needs_enhancement" when graph runs in parallel.

    Args:
        left (bool): The initial state or previous value.
        right (bool): The current state or new value.

    Returns:
        bool: The value of the right argument, indicating if an enhancement is needed.
    """
    return right


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    needs_enhancement: Annotated[bool, needs_enhancement_reducer]


# Helper function to create a node for a given agent
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

    # We convert the agent output into a format that is suitable to append to the global state
    if isinstance(result, ToolMessage):
        pass
    else:
        if "engineer" in name:
            result = AIMessage(
                **result.dict(exclude={"type", "name"}), name=name)
        else:
            result = AIMessage(**result.dict(exclude={"type", "name"}), name=name,
                               content=json.dumps(result.dict(exclude={"type", "name"})))

    return {
        "messages": [result],
        "needs_enhancement": False if name == "user_prompt_enhancer" else state["needs_enhancement"],
    }


# Function that initialize a llm client for a session
def initialize_llm_client(
    model: str = "gpt-4o-mini",
    streaming: bool = True,
    temperature: float = 0,
    top_p: float = 0.8,
) -> ChatOpenAI:
    """
    Initializes and returns a ChatOpenAI client for communication with OpenAI API with the specified parameters.

    Args:
        - model (str): The model name to use for the LLM client. Default is "gpt-4o-mini".
        - streaming (bool): Whether to enable streaming mode. Default is True.
        - temperature (float): The temperature setting for the model, controlling the randomness of the output. Default is 0.
        - top_p (float): The cumulative probability for nucleus sampling. Default is 0.8.

    Returns:
        - ChatOpenAI: An instance of the ChatOpenAI client initialized with the specified parameters.

    """

    # Get the OpenAI API key from the environment variables
    openai_api_key = os.getenv("DEV_OPENAI_KEY")

    try:
        # Initialize the LLM client
        llm = ChatOpenAI(
            model=model,
            api_key=openai_api_key,
            streaming=streaming,
            temperature=temperature,
            top_p=top_p,
        )

        logger.debug(
            f"LLM client ({temperature},{top_p},{streaming}) initialized successfully")

        # Return the initialized LLM client
        return llm

    except Exception as e:
        logger.error(f"Failed to initialize LLM client: {e}")
        return None


def answer_from_chroma(messages: list) -> str:
    """
    Retrieves and formats an answer from the Chroma database based on the provided messages.

    A special function dedicated to the phase 1 of chatbot flow.

    Args:
        - messages (list): A conversation between chatbot and user.

    Returns:
        - str: A formatted string containing the retrieved information and its source.

    """

    try:
        document = arun(get_retrieve_data(
            messages[-1]["content"], n_results=1))

        embedding = json.loads(document.text)

        logger.debug("Successfuly retrieved documents from Database")

        return (
            embedding["documents"][0]["content"]
            + "\n\n---\n\n"
            + "Source: "
            + embedding["documents"][0]["metadata"]["filename"]
        )

    except Exception as e:
        logger.error(f"Failed to retrieve documents: {e}")
        return "Failed to retrieve documents from Database. Please try again later or continue with another question."


def process_flow_output(output: list[AIMessage]) -> str:
    """
    Processes the output from a flow and formats it into a string.

    Args:
        - output (list[AIMessage]): A list of AIMessage objects containing the flow output.

    Returns:
        - str: A formatted string containing the answer and sources if available.

    """
    output_dict = json.loads(output["messages"][-1].content)

    if "sources" in output_dict and output_dict["sources"] != []:
        rag_answer = output_dict["answer"] + "\n\n---\n\n" + "Source: "
        for i in output_dict["sources"]:
            if i != output_dict["sources"][-1]:
                rag_answer += (i + ", ")
            else:
                rag_answer += i
    else:
        rag_answer = output_dict["answer"]

    return rag_answer


def build_webscrapes_subgraph(llm_client) -> str:
    """
    Builds and returns a subgraph for the embeddings retrieval from webscraper collection.

    This flow uses a prompt that creates a set of relevant keywords.

    Args:
        llm_client: The language model client used to spawn the webscrapes engineer agent.

    Returns:
        str: The compiled subgraph as a string representation.

    The function performs the following steps:
    1. Defines the tools required for web scraping.
    2. Creates a webscrapes engineer node using the provided language model client.
    3. Initializes a ToolNode with the defined tools.
    4. Constructs a StateGraph with an AgentState.
    5. Adds nodes and edges to the subgraph to define the workflow.
    6. Compiles the subgraph and returns it as a string.
    """

    tools = [webscrapes_retriever]

    webscrapes_engineer_node = functools.partial(
        agent_node, agent=spawn_webscrapes_engineer(llm_client), name="webscrapes_engineer"
    )
    python_runner = ToolNode(tools)

    subgraph = StateGraph(AgentState)

    subgraph.add_node("webscrapes_engineer", webscrapes_engineer_node)
    subgraph.add_node("python_runner", python_runner)

    subgraph.add_edge(START, "webscrapes_engineer")
    subgraph.add_edge("webscrapes_engineer", "python_runner")
    subgraph.add_edge("python_runner", END)

    subgraph = subgraph.compile()

    return subgraph


def build_documents_keywords_subgraph(llm_client) -> str:
    """
    Builds and returns a subgraph for the embeddings retrieval from knowledge collection.

    This flow uses a prompt that creates a set of relevant keywords.

    This function sets up a state graph with nodes for document engineering and Python execution.
    It connects these nodes to form a workflow that starts with a document engineering agent,
    followed by a Python runner, and ends the process.

    Args:
        llm_client: The language model client used to spawn the document engineering agent.

    Returns:
        str: The compiled subgraph as a string representation.
    """

    tools = [documents_retriever_keywords_prompt]

    documents_engineer_node = functools.partial(
        agent_node, agent=spawn_keywords_documents_engineer(llm_client), name="documents_engineer"
    )
    python_runner = ToolNode(tools)

    subgraph = StateGraph(AgentState)

    subgraph.add_node("documents_engineer", documents_engineer_node)
    subgraph.add_node("python_runner", python_runner)

    subgraph.add_edge(START, "documents_engineer")
    subgraph.add_edge("documents_engineer", "python_runner")
    subgraph.add_edge("python_runner", END)

    subgraph = subgraph.compile()

    return subgraph


def build_documents_mimic_prompt_subgraph(llm_client) -> str:
    """
    Builds and returns a subgraph for the embeddings retrieval from knowledge collection.

    This flow uses a prompt that mimics language of official documents.

    This function creates a state graph with nodes and edges representing the 
    document engineering and Python execution steps. It uses a language model 
    client to spawn a document engineer agent and sets up the necessary tools 
    for document retrieval.

    Args:
        llm_client: The language model client used to spawn the document engineer agent.

    Returns:
        str: The compiled subgraph representing the document mimic prompt process.
    """

    tools = [documents_retriever_mimic_prompt]

    documents_engineer_node = functools.partial(
        agent_node, agent=spawn_mimic_documents_engineer(llm_client), name="documents_engineer"
    )
    python_runner = ToolNode(tools)

    subgraph = StateGraph(AgentState)

    subgraph.add_node("documents_engineer", documents_engineer_node)
    subgraph.add_node("python_runner", python_runner)

    subgraph.add_edge(START, "documents_engineer")
    subgraph.add_edge("documents_engineer", "python_runner")
    subgraph.add_edge("python_runner", END)

    subgraph = subgraph.compile()

    return subgraph
