from langchain_openai import ChatOpenAI
from langchain.schema.runnable import Runnable
from langchain_core.prompts.prompt import PromptTemplate

from src.utils.agent_tools import webscrapes_retriever
from src.utils.data_models import RagResponse, UserPromptEnhancerResponse, RelevanceCheckerResponse, PreprocessedContext
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
    preprocessed_context = state["preprocessed_context"].model_dump_json()
    if preprocessed_context is None or preprocessed_context == "":
        preprocessed_context = "No auxiliary informations available."

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
            - Use auxiliary structure to better understand context.
            - If you cannot find requested information in context, answer that you do not know at the moment.

            3. **Ask additional questions**:
            - If you need more information to provide a complete answer, ask the user for clarification.

            4. **Clarity & Concision**:
            - Keep "answer" concise, professional, and informative.
            - **Thoroughly** analyze the context to provide a clear and accurate response.
            - Use a polite tone, as you are speaking to students and staff.

            ## AUXILIARY STRUCTURE
            {preprocessed_context}

            ## CONTEXT:
            {retrieved_context}
            """

    runnable_prompt = PromptTemplate.from_template(template)

    runnable_prompt = runnable_prompt.partial(
        retrieved_context=retrieved_context,
        query=query,
        conversation=conversation_messages,
        preprocessed_context=state["preprocessed_context"].model_dump_json()
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


def spawn_user_prompt_enhancer(llm: ChatOpenAI, state: dict) -> Runnable:
    """
    Creates and returns a user prompt enhancer agent using a provided language model (LLM).

    Args:
        - llm (ChatOpenAI): The language model to be used for creating the user prompt enhancer agent.

    Returns:
        - Runnable: The created user prompt enhancer agent.

    """
    query = get_user_query(state)

    template = """
        OBJECTIVE:
        You are a specialized LLM agent dedicated to refining user questions for educational and research contexts in the Faculty 
        of Electrical Engineering and Informatics at the Slovak University of Technology in Bratislava.

        ## User query: {query}

        ## GUARDRAIL INSTRUCTIONS

        1. You must respond in **valid JSON**, following the structure below exactly:

            {{
                "enhanced_input": "enhanced user input"
            }}

        2. Integrate relevant university-related terms and ensure each prompt aligns with the faculty’s academic and research scope.
        3. Maintain clarity, precision, and consistency when refining user input.
        """

    runnable_prompt = PromptTemplate.from_template(template)

    runnable_prompt = runnable_prompt.partial(
        query=query,
    )

    return runnable_prompt | llm.with_structured_output(UserPromptEnhancerResponse, method="json_mode")


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


def spawn_context_preprocessor(llm: ChatOpenAI, state: dict) -> Runnable:
    retrieved_context = get_retrieved_context(state)

    template = """
        You are Context Compressor, an expert pre-processor that transforms raw, multi-paragraph retrieval results into a compact, 
        loss-less briefing that downstream LLMs can ingest efficiently.

        ### Your goals (in priority order)

        1. Preserve every non-redundant fact  
        - Names, numbers, dates, quotations, causal links, and source attributions must not be lost or distorted.  
        2. Eliminate noise  
        - Strip filler words, rhetorical questions, promotional language, headers/footers, navigation text, and duplicated sentences.  
        3. Condense intelligently  
        - Merge semantically identical sentences; replace verbose phrases with precise terms; keep sentences ≤ 30 tokens when possible.  
        4. Structure for fast LLM scanning  
        - Output a predictable, sectioned format (see below) so later agents can pinpoint what they need without rereading everything.

        ## GUARDRAIL INSTRUCTIONS

        1. You must respond in **valid JSON**, following the structure below exactly:

        {{
            "topic": "abstract of the entire context",
            "key_points": ["Bullets of single idea / fact", "…"],
            "details_by_source": ["One line per distinct fact", "…"],
            "glossary": {{"abbr.":"one-line definition>"}}
        }}

        2. Guidelines:

        - **Topic**: Write a 2-to-4-sentence abstract of the entire context.
        - **Key points**: List the most important facts in bullet form.
        - **Details by source**: For each source, write a concise sentence for each distinct fact, one per line.
        - **Glossary**: Include abbreviations and their one-line definitions.

        ### Style guide

        - Neutral, declarative voice; no first-person, no opinions.    
        - Abbreviate consistently; define first time in GLOSSARY if not obvious.  
        - Never add content not present in the retrieval; never speculate.  

        ### THIS is the retrieved context for you to process:
        {retrieved_context}
        """
    runnable_prompt = PromptTemplate.from_template(template)

    runnable_prompt = runnable_prompt.partial(
        retrieved_context=retrieved_context
    )

    return runnable_prompt | llm.with_structured_output(PreprocessedContext, method="json_mode")
