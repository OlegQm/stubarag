from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate

from common.logging.global_logger import logger
from common.llm.llm_utils import initialize_llm_client

"""
A module for the conversation title generation.

"""


# Function that summarizes conversation content and creates a title for history menu
def conversation_title_agent(input: str, llm_used: str = "gpt-4o-mini") -> str:
    """
    Generates a concise and relevant title for a given conversation based on its content, context, and key themes.

    System message is used to provide instructions to the language model on how to generate the title.

    Args:
        - conversation_content (str): The content of the conversation for which the title is to be generated.
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
                Be minimalistic: Aim for a length of max 5 words.
                Output: A single sentence that serves as an effective title for the conversation. Never use quotation
                marks in your response.
            """
            ),
            HumanMessagePromptTemplate.from_template("{input}"),
        ]
    )

    # LLM with streaming disabled for title generation.
    llm = initialize_llm_client(llm_used, streaming=False, temperature=0.7, top_p=1)

    # Create the processing chain
    chain = prompt | llm | StrOutputParser()

    try:
        # Invoke the chain and wait for the result
        result = chain.invoke({"input": input})
        logger.debug(f"Generated title: {result}")
        # Return the generated title
        return result
    except Exception as e:
        logger.error(f"Failed to generate a title: {e}")
        return "Untitled Conversation"
