from langchain_openai import ChatOpenAI
from langchain.schema.runnable import Runnable
from langchain_core.prompts.prompt import PromptTemplate

from src.utils.agent_tools import webscrapes_retriever
from src.utils.data_models import RagResponse, RelevanceCheckerResponse
from src.utils.llm_utils import get_retrieved_context, get_conversation_messages, get_user_query

"""

A module for defining agents that can be used in the LLM workflow.

"""

### DEFINITIONS OF AGENTS AND AGENT NODES ###


def spawn_rag_agent(llm: ChatOpenAI, state: dict) -> Runnable:
    """
    Spawns a RAG (Retrieval-Augmented Generation) agent named Agent Kováč, specialized in supporting students at the 
    Faculty of Electrical Engineering and Informatics (FEI) at the Slovak University of Technology in Bratislava (STU Bratislava).

    Args:
        - llm: The language model to be used by the RAG agent.

    Returns:
        A configured RAG agent instance.
    """
    retrieved_context = get_retrieved_context(state)
    conversation_messages = get_conversation_messages(state)
    query = get_user_query(state)

    template = """
You are Agent Kováč, a specialized chatbot dedicated to supporting students at the
Faculty of Electrical Engineering and Informatics (FEI) at the Slovak University of Technology
in Bratislava (STU Bratislava). Your purpose is to provide academic advice, administrative support,
information resources, and campus life details to students.

## Previous conversation: {conversation}
## User query: {query}

## GUARDRAIL INSTRUCTIONS

1. You must respond in **valid JSON**, following the structure below exactly:

{{
    "answer": "Your concise, final response to the user's query.",
    "sources": ["List", "of", "document names", "or", "websites"]
}}

2. **No Fabrication Clause**:
- You must **not** invent details or create new sources.
- Your response **must** be based on the context.
- If you cannot find requested information in context, answer that you do not know at the moment.

3. **Ask additional questions**:
- If you need more information to provide a complete answer, ask the user for clarification.

4. **Clarity & Concision**:
- Keep "answer" concise, professional, and informative.
- **Thoroughly** analyze the context to provide a clear and accurate response.
- Use a polite tone, as you are speaking to students and staff.

## CONTEXT:
{retrieved_context}
"""

    runnable_prompt = PromptTemplate.from_template(template)

    runnable_prompt = runnable_prompt.partial(
        retrieved_context=retrieved_context,
        query=query,
        conversation=conversation_messages,
    )

    return runnable_prompt | llm.with_structured_output(RagResponse, method="json_mode")


def spawn_webscrapes_engineer(llm: ChatOpenAI, state: dict) -> Runnable:
    """
    Creates an embeddings engineer agent that refines user queries for better embeddings retrieval and uses an embeddings retriever tool to retrieve relevant documents.

    Args:
        llm (ChatOpenAI): The language model to be used for query refinement.

    Returns:
        Runnable: An agent that enhances user queries and retrieves relevant documents using the embeddings retriever tool.
    """
    conversation_messages = get_conversation_messages(state)
    query = get_user_query(state)

    template = """
            You are a knowledge engineer specializing in topics related to FEI STU.
            Your job is to refine the user query to improve retrieval from the vector database,
            and then you must call the 'webscrapes_retriever' tool exactly once with that refined query.

            ## User question: {query}
            ## Previous conversation: {conversation}

            Remember: you do not provide a final answer to the user; your job is to retrieve relevant documents.
            """

    runnable_prompt = PromptTemplate.from_template(template)

    runnable_prompt = runnable_prompt.partial(
        query=query,
        conversation=conversation_messages
    )

    return runnable_prompt | llm.bind_tools([webscrapes_retriever], parallel_tool_calls=True)


def spawn_relevance_checker(llm: ChatOpenAI, state: dict) -> Runnable:
    """
    Creates and returns a relevance checker agent using the provided language model.

    The relevance checker agent is designed to assess the relevance of user intentions
    to the specified purpose of the flow, which includes providing academic advice,
    administrative support, information resources, and campus life details to students.

    Parameters:
        - llm (ChatOpenAI): The language model to be used by the relevance checker agent.

    Returns:
        - Runnable: A runnable relevance checker agent.

    """
    conversation_messages = get_conversation_messages(state)
    query = get_user_query(state)

    template = """
        ## OBJECTIVE:
        You are a part of RAG agentic workflow focused on providing academic advice, administrative support,
        information resources, and campus life details to students of FEI STU.
        Your job is to check whether the user query is relevant.

        ## User query: {query}
        ## Previous conversation: {conversation}

        ## GUARDRAIL INSTRUCTIONS

            1. You must respond in **valid JSON**, following the structure below exactly:

            {{
                "found_relevance": "Yes or No",
            }}

            2. **Analyze the user query** and determine if it is relevant.
                - If the user query is about gathering informations:
                    - Set "found_relevance": "Yes".
                    - End the response.
                - If the user query is about help with assignment, exam, generate code or any other irrelevant task:
                    - Set "found_relevance": "No".
                    - End the response.
            """
    runnable_prompt = PromptTemplate.from_template(template)

    runnable_prompt = runnable_prompt.partial(
        query=query,
        conversation=conversation_messages
    )

    return runnable_prompt | llm.with_structured_output(RelevanceCheckerResponse, method="json_mode")
