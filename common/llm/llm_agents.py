from pydantic import BaseModel, Field
from typing import List
from langchain_openai import ChatOpenAI
from langchain.schema.runnable import Runnable
from langchain_core.prompts.chat import ChatPromptTemplate, MessagesPlaceholder, SystemMessage, AIMessage

from common.llm.agent_tools import webscrapes_retriever, documents_retriever_mimic_prompt, documents_retriever_keywords_prompt

"""

A module for defining agents that can be used in the LLM workflow.

"""


### LLM AGENT TEMPLATES ###


def create_thinking_agent(llm: ChatOpenAI, system_message: str, output_data_model: BaseModel) -> Runnable:
    """
    Creates a thinking agent using a language model and a system message.

    This type of agent is designed to think and generate responses based 
    on the provided system message and informations from other agents.

    Args:
        llm (ChatOpenAI): The language model to be used for the agent.
        system_message (str): The system message to be included in the prompt.

    Returns:
        Runnable: A runnable object that represents the thinking agent.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are AI assistant, collaborating with other assistants."
                "{system_message}",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    prompt = prompt.partial(system_message=system_message)
    return prompt | llm.with_structured_output(output_data_model, method="json_mode")


def create_working_agent(llm: ChatOpenAI, tools: list[callable], system_message: str) -> Runnable:
    """
    Creates a working agent using a language model and a set of tools.

    This type of agent use the provided tools to perform specific tasks.

    Args:
        - llm (ChatOpenAI): The language model to be used.
        - tools (list[callable]): A list of callable tools that the agent can use.
        - system_message (str): A system message to be included in the prompt.

    Returns:
        - Runnable: A runnable object that represents the configured agent.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content="""You are AI assistant, collaborating with other assistants. 
                **Do not** answer the question. Use the tools to do only your task. 
                You have access to the following tools: {tool_names}.\n{system_message}"""),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    if len(tools) > 0:
        prompt = prompt.partial(
            tool_names=", ".join([tool.name for tool in tools]),
            system_message=system_message,
        )
        return prompt | llm.bind_tools(tools, parallel_tool_calls=True)
    else:
        prompt = prompt.partial(
            tool_names="There are no tools for you.", system_message=system_message
        )
        return prompt | llm


### DEFINITIONS OF AGENTS AND AGENT NODES ###

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


def spawn_rag_agent(llm: ChatOpenAI) -> Runnable:
    """
    Spawns a RAG (Retrieval-Augmented Generation) agent named Agent Kováč, specialized in supporting students at the 
    Faculty of Electrical Engineering and Informatics (FEI) at the Slovak University of Technology in Bratislava (STU Bratislava).

    Args:
        - llm: The language model to be used by the RAG agent.

    Returns:
        A configured RAG agent instance.
    """

# A LLM agent that put the final answer together using the information from other agents and RAG principles.
    rag_agent = create_thinking_agent(
        llm,
        system_message="""You are Agent Kováč, a specialized chatbot dedicated to supporting students at the
                        Faculty of Electrical Engineering and Informatics (FEI) at the Slovak University of Technology
                        in Bratislava (STU Bratislava). Your purpose is to provide academic advice, administrative support,
                        information resources, and campus life details to students.

                        ## GUARDRAIL INSTRUCTIONS

                        1. You must respond in **valid JSON**, following the structure below exactly:

                        {
                            "answer": "Your concise, final response to the user's query.",
                            "sources": ["List", "of", "document names", "or", "websites"]
                        }

                        2. **No Fabrication Clause**:
                        - You must **not** invent details or create new sources.
                        - Your response **must** be based on the information provided by other agents or tools.

                        3. **Ask additional questions**:
                        - If you need more information to provide a complete answer, ask the user for clarification.

                        4. **Context Prioritization**:
                        - If the information can be found in both documents and web sources, prioritize the web sources.

                        5. **Clarity & Concision**:
                        - Keep "answer" concise, professional, and informative.
                        - **Thoroughly** analyze the information from other agents to provide a clear and accurate response.
                        - Use a polite tone, as you are speaking to students and staff.
        """,
        output_data_model=RagResponse)
    return rag_agent


def spawn_mimic_documents_engineer(llm: ChatOpenAI) -> Runnable:
    """
    Creates an embeddings engineer agent that refines user queries for better embeddings retrieval and uses an embeddings retriever tool to retrieve relevant documents.

    Args:
        llm (ChatOpenAI): The language model to be used for query refinement.

    Returns:
        Runnable: An agent that enhances user queries and retrieves relevant documents using the embeddings retriever tool.
    """
    # A LLM agent that enhance user query for better embeddings retrieval and then uses embeddings retriever tool to retrieve relevant documents.
    embeddings_enginner = create_working_agent(
        llm,
        [documents_retriever_mimic_prompt],
        system_message="""
                You are a knowledge engineer specializing in topics related to FEI STU.
                Your job is to refine the user query to improve retrieval from the vector database,
                and then you must call the 'webscrapes_retriever' tool exactly once with that refined query.

                Remember: you do not provide a final answer to the user; your job is to retrieve relevant documents.
                """,
    )
    return embeddings_enginner


def spawn_keywords_documents_engineer(llm: ChatOpenAI) -> Runnable:
    """
    Creates an embeddings engineer agent that refines user queries for better embeddings retrieval and uses an embeddings retriever tool to retrieve relevant documents.

    Args:
        llm (ChatOpenAI): The language model to be used for query refinement.

    Returns:
        Runnable: An agent that enhances user queries and retrieves relevant documents using the embeddings retriever tool.
    """
    # A LLM agent that enhance user query for better embeddings retrieval and then uses embeddings retriever tool to retrieve relevant documents.
    embeddings_enginner = create_working_agent(
        llm,
        [documents_retriever_keywords_prompt],
        system_message="""
                You are a knowledge engineer specializing in topics related to FEI STU.
                Your job is to refine the user query to improve retrieval from the vector database,
                and then you must call the 'webscrapes_retriever' tool exactly once with that refined query.

                Remember: you do not provide a final answer to the user; your job is to retrieve relevant documents.
                """,
    )
    return embeddings_enginner


def spawn_webscrapes_engineer(llm: ChatOpenAI) -> Runnable:
    """
    Creates an embeddings engineer agent that refines user queries for better embeddings retrieval and uses an embeddings retriever tool to retrieve relevant documents.

    Args:
        llm (ChatOpenAI): The language model to be used for query refinement.

    Returns:
        Runnable: An agent that enhances user queries and retrieves relevant documents using the embeddings retriever tool.
    """
    # A LLM agent that enhance user query for better embeddings retrieval and then uses embeddings retriever tool to retrieve relevant documents.
    webscrapes_enginner = create_working_agent(
        llm,
        [webscrapes_retriever],
        system_message="""
            You are a knowledge engineer specializing in topics related to FEI STU.
            Your job is to refine the user query to improve retrieval from the vector database,
            and then you must call the 'webscrapes_retriever' tool exactly once with that refined query.

            Remember: you do not provide a final answer to the user; your job is to retrieve relevant documents.
        """,
    )
    return webscrapes_enginner


class UserPromptEnhancerResponse(BaseModel):
    """
    UserPromptEnhancerResponse is a model that represents the response of an user prompt enhancer agent.

    Attributes:
        enhanced_input (str): Enhanced user input.
    """
    enhanced_input: str = Field(..., description="Enhanced user input")


def spawn_user_prompt_enhancer(llm: ChatOpenAI) -> Runnable:
    """
    Creates and returns a user prompt enhancer agent using a provided language model (LLM).

    Args:
        - llm (ChatOpenAI): The language model to be used for creating the user prompt enhancer agent.

    Returns:
        - Runnable: The created user prompt enhancer agent.

    """
    # A LLM agent that enhances user prompt. Enhanced prompt is more focused on education and academic context.
    user_prompt_enhancer = create_thinking_agent(
        llm,
        system_message="""
            OBJECTIVE:
            You are a specialized LLM agent dedicated to refining user questions for educational and research contexts in the Faculty 
            of Electrical Engineering and Informatics at the Slovak University of Technology in Bratislava.

            ## GUARDRAIL INSTRUCTIONS

            1. You must respond in **valid JSON**, following the structure below exactly:

                {
                    "enhanced_input": "ehanced user input"
                }

            2. Integrate relevant university-related terms and ensure each prompt aligns with the faculty’s academic and research scope.
            3. Maintain clarity, precision, and consistency when refining user input.
            """,
        output_data_model=UserPromptEnhancerResponse,
    )
    return user_prompt_enhancer


class RelevanceCheckerResponse(BaseModel):
    """
    RelevanceCheckerResponse is a model that represents the response from a relevance checker agent.

    Attributes:
        found_relevance (str): Indicates whether relevance was found ('Yes' or 'No').
        answer (str): Polite decline of user request with the reason for the decline.
    """
    found_relevance: str = Field(..., pattern="^(Yes|No)$",
                                 description="Indicates whether relevance was found ('Yes' or 'No').")
    answer: str = Field(
        ..., description="Polite decline of user request with the reason for the decline.")


def spawn_relevance_checker(llm: ChatOpenAI) -> Runnable:
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
    relevance_checker = create_thinking_agent(
        llm,
        system_message="""
            ## OBJECTIVE:
            You are a relevance checker tasked with assesing the relevance of the user intentions to the purpose of this flow.

            ## PURPOSE OF FLOW
             - Help students and employees of the Faculty of Electrical Engineering and Informatics (FEI) at the Slovak University of 
             Technology (STU) in Bratislava.

            ## GUARDRAIL INSTRUCTIONS

                1. You must respond in **valid JSON**, following the structure below exactly:

                {
                    "found_relevance": "Yes or No",
                    "answer": "Polite decline of user request with the reason for the decline."
                }

                2. **Scope & Context Checks**:
                - If you find the user's query **not** relevant to the purpose of this flow:
                    - Set "found_relevance": "No".
                    - Set "answer" to a polite decline with the explanation.
                    - End the response.
                - If the user requests assignment help, exam solutions, or tasks unrelated to FEI STU (e.g., code debugging, creative writing):
                    - Set "found_relevance": "No".
                    - Set "answer" to a polite decline with the explanation.
                    - End the response.
                - **If the user’s query involves any matter directly related to FEI STU (including questions about dates, awards, course enrollment, 
                tuition fees, exams, schedules, departmental contacts, events, scholarships, or any administrative process), it is relevant.**  

                Examples of relevant user questions:
                - "Koľko kreditov potrebujem na prechod do ďalšieho semestra?"
                - "Kto je predseda Akademického senátu?"
                - "Kedy dostanem cenu dekana ?"
                - "Kde nájdem rozvrh skúšok ?"

                In these cases:
                    - Set "found_relevance": "Yes".
                    - Set "answer": "".
                    - End the response.

                - **If there is uncertainty** but the question seems to concern **any aspect** of FEI STU or 
                could be answered by the study department or faculty administration (e.g., questions about policies, 
                procedures, events, official documents, deadlines, awards):
                    - **Lean towards relevance** and set "found_relevance": "Yes".
                    - Set "answer": "".
                    - End the response.
        """,
        output_data_model=RelevanceCheckerResponse,
    )
    return relevance_checker


class ContextCheckerResponse(BaseModel):
    """
    ContextCheckerResponse is a model that represents the response from a context checker agent.

    Attributes:
        context_available (str): Indicates whether context was found ('Yes' or 'No').
        answer (str): Polite decline of user request with the reason for the decline.
    """
    context_available: str = Field(..., pattern="^(Yes|No)$",
                                   description="Indicates whether context was found ('Yes' or 'No').")
    answer: str = Field(
        ..., description="Polite decline of user request with the reason for the decline.")


def spawn_context_checker(llm: ChatOpenAI) -> Runnable:
    """
    Creates and returns a context checker agent using the provided language model.

    The context checker agent is responsible for assessing the relevance of retrieved information
    to the user's intention. It follows specific guardrail instructions to ensure the response is
    in valid JSON format and adheres to the given structure.

    Args:
        - llm (ChatOpenAI): The language model to be used by the context checker agent.

    Returns:
        - Runnable: A runnable context checker agent.

    """
    context_checker = create_thinking_agent(
        llm,
        system_message="""
            ## OBJECTIVE:
            You are a context availability checker tasked with assesing the relevance of the retrieved
            informations to the user intention.

            ## GUARDRAIL INSTRUCTIONS

                1. You must respond in **valid JSON**, following the structure below exactly:

                {
                    "context_available": "Yes or No",
                    "answer": "Polite decline of user request with the reason for the decline."
                }

                2. **Analyze all documents** in the chat context and determine if they are relevant to the user's query.
                - Is it possible to provide a relevant answer based on the retrieved information?: 
                    - Set "context_available": "Yes".
                    - Set "answer": "".
                    - End the response.
                - If the retrieved documents do not contain information user is looking for:
                    - Set "context_available": "No".
                    - Set "answer" to a polite decline stating that you could not find any relevant informations this time.
                    - End the response.
        """,
        output_data_model=ContextCheckerResponse,
    )
    return context_checker


### UNUSED AGENTS FOLLOWS ###

# answer_grader = create_servant_agent(
#     grading_llm,
#     [],
#     system_message="""You are a grader assessing whether an answer addresses / resolves a question \n
#         Give a binary score 'yes' or 'no'. Yes' means that the answer resolves the question. \n
#         User question: \n\n {question} \n\n LLM generation: {generation}
#         """,
# )
# answer_grader_node = functools.partial(
#     agent_node, agent=answer_grader, name="answer_grader"
# )


# phase_shifter = create_servant_agent(
#     grading_llm,
#     [],
#     system_message="""You are a llm agent dedicated to deciding whether user is satisfied with the provided answer based on \n
#         response to the question "Did I answer ?" \n

#         """,
# )
# phase_shifter_node = functools.partial(
#     agent_node, agent=phase_shifter, name="phase_shifter"
# )
