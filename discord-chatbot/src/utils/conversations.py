import discord

from common.logging.global_logger import logger
from src.session import history
from common.llm.discord_adapter import DiscordAdapter

# Initialize DiscordAdapter for communication with LLM
llm_adapter = DiscordAdapter()


async def get_response(conversation_context: list) -> str:
    """
    Prompt the model with the user input and return the response.
    Context is a list of messages that the model uses to generate a response.

    Args:
        - conversation_context (list): List of messages to be passed to the model

    Returns:
        - str: The model's response to the user input
    """

    response = await llm_adapter.send_query(conversation_context)
    return response


async def get_thread_history(message: discord.Message, num_messages: int) -> list:
    """
    Builds the conversation history of a given thread. The conversation history
    format is a list of dictionaries, where each dictionary contains the role
    of the participant and the content of the message.
    e.g. [{"role": "user", "content": "Hello!"}, {"role": "assistant", "content": "Hi!"}]

    Args:
        - message (discord.Message): The message object that triggered the bot
        - num_messages (int): The number of messages to retrieve from the channel

    Returns:
        - list: The conversation history of the given thread.
    """

    thread = message.channel
    history = []
    # Get the last n messages from the thread
    async for thread_message in thread.history(limit=num_messages):
        if thread_message.id == message.id:
            # Skip the message that triggered the thread
            continue
        if thread_message.embeds:
            # Message contains an embed is context separator
            break
        if thread_message.author.bot:
            history.append(
                {"role": "assistant", "content": thread_message.content}
            )
        else:
            history.append(
                {"role": "user", "content": thread_message.content}
            )
    history.reverse()
    return history
        

async def get_reply_chain(message: discord.Message, num_messages: int) -> list:
    """
    Builds the conversation history leading up to the original message.
    The conversation history format is a list of dictionaries, where each dictionary
    contains the role of the participant and the content of the message.
    
    Args:
        - message (discord.Message): The message object for which to build the reply chain
        - num_messages (int): The maximum number of messages to include in the chain

    Returns:
        - list: A list of message contents leading up to the original message
    """

    channel = message.channel
    history = []
    current_message = message.reference.resolved
    while current_message and len(history) < num_messages:
        if current_message.author.bot:
            history.append(
                {"role": "assistant", "content": current_message.content}
            )
        else:
            history.append(
                {"role": "user", "content": current_message.content}
            )
        if current_message.reference:
            message_id = current_message.reference.message_id
            current_message = await channel.fetch_message(message_id) 
        else:
            break
    history.reverse()
    return history


async def is_reply_to_bot(client: discord.Client, message: discord.Message) -> bool:
    """
    Checks if the message is a reply to a bot message.

    Args:
        - client (discord.Client): The Discord client instance
        - message (discord.Message): The message object to check

    Returns:
        - bool: True if the message is a reply to a bot message, False otherwise
    """

    if not message.reference:
        return False
    referenced_message = await message.channel.fetch_message(message.reference.message_id)
    return referenced_message.author == client.user


def save_message(messages: list, user_id: str) -> None:
    """
    Saves a conversation record to the MongoDB collection.

    Args:
        - messages (list): The conversation content to save
        - user_id (str): The user ID associated with the conversation

    Returns:
        None
    """

    history.save_conversation(messages, user_id)
