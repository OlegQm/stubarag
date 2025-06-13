import os
from asyncio import run as run_async

import openai
from common.llm import embeddings
from chat_app.session import handlers
from langchain.memory import ConversationBufferMemory
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import Runnable, RunnableLambda
from langchain_community.callbacks.manager import get_openai_callback
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_openai import ChatOpenAI


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

    # Initialize the LLM client
    llm = ChatOpenAI(
        model=model,
        api_key=openai_api_key,
        streaming=streaming,
        temperature=temperature,
        top_p=top_p,
    )

    # Return the initialized LLM client
    return llm


# Function that summarizes conversation content and creates a title for history menu
def create_title_for_conversation(conversation_content: list, llm: ChatOpenAI) -> str:
    """
    Generates a concise and relevant title for a given conversation based on its content, context, and key themes.

    System message is used to provide instructions to the language model on how to generate the title.

    Args:
        - conversation_content (list): The content of the conversation for which the title is to be generated.
        - llm (ChatOpenAI): The LLM client used to generate the title.

    Returns:
        - str: A single sentence that serves as an effective title for the conversation.

    """

    # Define the prompt template
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content="""
                Generate a concise and relevant title for a given conversation based on its content, context, and 
                key themes. Title must be in the same language as most of the conversation.
                Instructions:
                Analyze Content: Carefully review the provided conversation to identify the main topics, key points, 
                and overall context.
                Identify Core Themes: Determine the primary themes or subjects discussed in the conversation. Focus 
                on the most significant aspects that encapsulate the conversation's purpose or conclusion.
                Create the Title: Make the title clear, concise, and reflective of the conversation's essence. 
                Aim for a length of max 5 words.
                Ensure the title is engaging and informative, giving a clear idea of what the conversation is about.
                Avoid overly generic titles; strive for specificity and relevance.
                Tone and Style: Match the tone of the title to the nature of the conversation (e.g., formal, casual, 
                technical, or creative).
                Output: A single sentence that serves as an effective title for the conversation. Never use quotation 
                marks in your response.
            """
            ),
            HumanMessagePromptTemplate.from_template("{input}"),
        ]
    )

    # Create the processing chain
    chain = prompt | llm | StrOutputParser()

    # Invoke the chain and wait for the result
    result = chain.invoke({"input": conversation_content})

    # Return the generated title
    return result


# Function that generate keywords and main points of user query
# for effective embeddings retrieval
def summarize_query_for_embeddings_retrieval(
    user_input: HumanMessage, conversation_history: list, llm: ChatOpenAI
) -> str:
    """
    Enhances a user query for better and efficient retrieval of embeddings from ChromaDB.

    Args:
        - user_input (HumanMessage): The original query input from the user.
        - conversation_history (ConversationBufferMemory): The history of the conversation to provide context.
        - llm (ChatOpenAI): The LLM client used to process and enhance the query.

    Returns:
        - str: The enhanced query optimized for embeddings retrieval form ChromaDB.

    """

    # Prepare the prompt for enhancement process
    user_input = "Enhance this query: " + user_input

    # Define the prompt template
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content="""
                You are a large language model specifically designed to enhance user queries related to universities and academic studies. 
                Your sole purpose is to refine and enrich the user's input, transforming it into a more detailed and precise query. 
                This enhanced query will be optimized for processing by another language model, which will handle the actual response. 
                You must not provide answers to the user's original query. 

                Instructions:
                          
                - Focus on Faculty of Electrical Engineering and Informatics of Slovak University of Technology in Bratislava (FEI STU): If some university or
                faculty is mentioned in input query, it is always Faculty of Electrical Engineering and Informatics or Slovak University of Technology in Bratislava.
                If name of academic facility is not mentioned in query, consider it as FEI STU.

                - Focus on Enhancement Only: Your task is to analyze the user's input and create a more comprehensive query that better captures the intent. 
                Do not provide any direct answers or solutions.

                - Understand User Intent: Thoroughly understand the user's underlying intent, particularly in the context of academic studies, universities, or related topics.

                - Add Relevant Context: If the original query is vague, add necessary details to specify the academic content, such as research papers, 
                course descriptions, or university information. Include relevant keywords related to common academic themes like degree programs, faculty expertise, 
                research areas, campus life, and study resources.

                - Clarify Academic Terms: Expand abbreviations or acronyms related to education (e.g., convert "PhD" to "Doctor of Philosophy"). Provide complete names for university departments, degrees, 
                or academic subjects when only partial terms are given.

                - Incorporate Related Keywords: Enhance the query by adding synonyms or related terms that might improve the searchability in ChromaDB, 
                such as using "academic research" instead of "thesis work."

                - Structure the Query for Precision: Organize the query clearly to separate different components, such as the university name, program type, or study level. 
                Prioritize the most relevant aspects if the query involves multiple topics.

                - Preserve User Intent: While enhancing the query, ensure that the original user intent is preserved and not overly complicated.

                Examples:

                User Input: "stipends for PhD students"
                Enhanced Query: "Information on stipends available for PhD students at Faculty of Electrical Engineering and Informatics, including stipend amounts, eligibility criteria, funding sources, and differences by country and university."

                User Input: "What are some places to eat?"
                Enhanced Query: "List of recommended places to eat near Faculty of Electrical Engineering and Informatics, including popular cafes, student-friendly restaurants, campus dining halls, and options for various dietary preferences."

                User Input: "How should my thesis look like?"
                Enhanced Query: "Guidelines for formatting and structuring a thesis at Faculty of Electrical Engineering and Informatics, including recommended layout, section organization, citation styles, length requirements, and visual elements like tables and figures, specific to academic standards at universities."

                Remember: Your output is the enhanced query only. Output query must be in Slovak language. Do not provide any answers or engage in any other tasks.

            """
            ),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{input}"),
        ]
    )

    # Create the processing chain
    chain = (
        RunnableLambda(
            lambda inputs: {"input": inputs["input"], "history": conversation_history}
        )
        | prompt
        | llm
        | StrOutputParser()
    )

    # Invoke the chain and wait for the result
    result = chain.invoke({"input": user_input})

    # Return the enhanced query
    return result


# Function thath builds LangChain chain with conversation history and RAG context
def setup_chain(
    user_query: HumanMessage,
    main_llm: ChatOpenAI,
    aux_llm: ChatOpenAI,
    memory: ConversationBufferMemory,
    translation_sources: str = "Sources",
) -> Runnable:
    """
    Sets up a Langchain chain for processing the user query and generating a response
    based on the system prompt, conversation history and RAG context.

    Args:
        - user_query (HumanMessage): The query from the user.
        - main_llm (ChatOpenAI): The main language model used for generating responses.
        - aux_llm (ChatOpenAI): An auxiliary language model used for summarizing the query.
        - memory (ConversationBufferMemory): A memory object to load and store conversation history.
        - translation_sources (str): The source of the translation for citation. Default is "Sources".

    Returns:
        - chain (Runnable): A runnable chain that processes the user query and generates a response.

    """

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=f"""
                    You are FEI RAGbot, a specialized chatbot dedicated to supporting students at the 
                    Faculty of Electrical Engineering and Informatics (FEI) at the Slovak University of Technology 
                    in Bratislava (STU Bratislava). Your expertise is focused solely on providing accurate, detailed, 
                    and up-to-date information related to studies at FEI STU Bratislava. This includes, but is not limited to:
                    Academic Advice: Offering guidance on courses, exams, and academic pathways within FEI.
                    Administrative Support: Assisting with registration procedures, deadlines, and faculty-specific policies.
                    Information Resources: Information on available study materials, library access, and extracurricular activities.
                    Campus Life: Details about facilities, events, and student organizations within FEI STU.
                              
                    You are not equipped to provide information beyond the scope of FEI STU Bratislava. If a query falls outside 
                    this domain, politely inform the user that your expertise is limited to university and study-related matters 
                    within FEI. You always base your response on the context provided. If no relevant context or data 
                    is available in provided context, respond that you couldn't find an answer to the query at this time.
                    Never respond to the query if you cannot backup your answer with provided context !
                              
                    If user asks you to help him with his assigment, reformat code, or do any other irrelevant 
                    task that do not include obtaining informations about FEI STU, respond that you are just an information 
                    provider. Never provide anyone with code or complete solution of any assigment or exam question ! 
                            
                    As an academic chatbot, you must always cite your sources of information. This is an example of right citation:
                              
                    "Your answer to user query here\n\n---\n\n*{translation_sources}: some_document.pdf, other_document.pdf*" #st.session_state.translator("Sources")
 
                    Do not duplicate sources. If user query is not factual but informal, do not include sources.

                    Your goal is to be a reliable, context-aware resource for students, ensuring they receive 
                    precise and relevant information to enhance their academic journey at FEI STU Bratislava.
                    
                """
            ),
            ("user", "This is provided context: {context}"),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{input}"),
        ]
    )

    # Load the content of LLM memory buffer
    memory_content = memory.load_memory_variables({})
    conversation_history = memory_content["history"]

    # Summarize the user query for embeddings retrieval
    vector_search_keywords = summarize_query_for_embeddings_retrieval(
        user_query, conversation_history, aux_llm
    )
    # Retrieve embeddings from ChromaDB
    vector_query_result = run_async(
        embeddings.get_retrieve_data(vector_search_keywords, n_results=4)
    )

    # Create the processing chain
    chain = (
        # Set chain variables
        RunnableLambda(
            lambda inputs: {
                "input": inputs["input"],
                "context": vector_query_result.text,
                "history": conversation_history,
            }
        )
        | prompt
        | main_llm
        | StrOutputParser()
    )

    # Return the processing chain
    return chain


# Function to ask LLM. Returns response string
def send_query(
    user_query: HumanMessage,
    main_llm: ChatOpenAI,
    aux_llm: ChatOpenAI,
    memory: ConversationBufferMemory,
    stream_handler: callable = None,
    translation_sources: str = "Sources",
) -> str:
    """
    Get a response to the user query from LLM.

    Args:
        - user_query (HumanMessage): The query input from the user.
        - main_llm (ChatOpenAI): The main language model to be used for conversation with user.
        - aux_llm (ChatOpenAI): The auxiliary language model for creative side tasks.
        - memory (ConversationBufferMemory): The memory object to be used in the chain.
        - stream_handler (callable, optional): A callback function for handling streaming responses. Defaults to None.
        - translation_sources (str): The source of the translation for citation. Default is "Sources".

    Returns:
        - str: The LLM response to the user query.

    Raises:
        - openai.AuthenticationError: If the API key is not provided.
        - openai.APIConnectionError: If the connection to the language model is lost.

    """

    # Set up the processing chain
    chain = setup_chain(user_query, main_llm, aux_llm, memory, translation_sources=translation_sources)

    try:
        # Invoke the chain and get the response
        result = chain.invoke(
            {"input": user_query},
            # Only LLM responses to user query are streamed
            ({"callbacks": [stream_handler]} if stream_handler is not None else None),
        )
        # Return the response
        return result

    except openai.AuthenticationError:
        print(
            f"[{handlers.timestamp()} : {__name__} - {setup_chain.__name__}] API key not provided"
        )
        handlers.missing_API_key()

    except openai.APIConnectionError:
        print(
            f"[{handlers.timestamp()} : {__name__} - {setup_chain.__name__}] Lost connection with LLM"
        )
        handlers.lost_API_connection()


# Sends querry and prints how many tokens were spent
def count_tokens(user_query: HumanMessage, chain: Runnable) -> str:
    """
    Counts the number of tokens spent during the invocation of a chain with a user query.

    Args:
        - user_query (HumanMessage): The query input from the user.
        - chain (Runnable): The chain object that processes the user query.

    Returns:
        - str: The response from the chain after processing the user query.

    Prints:
        - The total number of tokens spent during the invocation.

    """

    with get_openai_callback() as cb:
        result = chain.invoke({"input": user_query})

        print(f"Spent a total of {cb.total_tokens} tokens")

    return result["response"]


# Function that loads conversation content to the memory buffer
def load_memory(
    conversation_content: list, memory: ConversationBufferMemory
) -> ConversationBufferMemory:
    """
    Load conversation history into LLM conversation memory buffer.

    This function takes conversation content and a memory object, processes the
    conversation content to extract user inputs and corresponding outputs, and
    populates the memory with this context history.

    Args:
        - conversation_content (list): A list of dictionaries representing the conversation history.
        - memory (ConversationBufferMemory): The memory object to be populated with the conversation history.

    Returns:
        - memory (ConversationBufferMemory): The memory object populated with the conversation history.

    """

    history_builder = []

    # Convert context into a format suitable for ConversationBufferMemory
    for msg in conversation_content:
        if msg["role"] == "user":
            input_msg = msg["content"]
        else:
            output_msg = msg["content"]
            history_builder.append({"input": input_msg, "output": output_msg})

    # Populate the memory with context history
    for pair in history_builder:
        inputs = {"input": pair["input"]}
        outputs = {"output": pair["output"]}
        # Save each PROMPT - ANSWER pair to memory
        memory.save_context(inputs, outputs)

    # Return the ConversationBufferMemory object
    return memory


# Wrapper for load_memory()
# Function that appends last prompt and llm reply pair to conversation buffer
def append_to_memory(
    prompt_reply_pair: list, memory: ConversationBufferMemory
) -> ConversationBufferMemory:
    """
    Wrapper for load_memory() function.

    Appends a prompt-reply pair to the memory.

    Args:
        - prompt_reply_pair (list): A list containing the prompt and the corresponding reply.
        - memory (ConversationBufferMemory): The current memory to which the prompt-reply pair will be appended.

    Returns:
        - memory (ConversationBufferMemory): The updated memory with the new prompt-reply pair included.

    """

    # Load the prompt-reply pair into the memory
    memory = load_memory(prompt_reply_pair, memory)

    # Return the updated memory
    return memory
