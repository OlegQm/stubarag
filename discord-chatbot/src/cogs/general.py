import discord

from src.utils.views import ButtonsView
from src.utils import conversations
from common.logging.global_logger import logger
from discord import Embed



async def private_message(message: discord.Message, client: discord.Client) -> None:
    """
    Responds to a private message in DM.

    Args:
        - message (discord.Message): The message object

    Returns:
        None
    """

    logger.info(f'[DM][{message.author.name}]: "{message.content}"')
    await message.channel.typing()
    # Ensure only the last message in the DM contains the button by removing old views
    async for msg in message.channel.history(limit=10):
        if msg.author == client.user and msg.components:
            await msg.edit(view=None)
    # Discord typing indicator while bot is processing the message
    if message.type == discord.MessageType.reply:
        conversation_context = await conversations.get_reply_chain(message, 10)
    else:
        conversation_context = await conversations.get_thread_history(message, 10)
    try:
        conversation_context.append({"role": "user", "content": message.content})
        logger.debug(f"Conversation context: {conversation_context}")
        ai_response = await conversations.get_response(conversation_context)
    except Exception as e:
        logger.error(f"Error when getting response: {e}")
        ai_response = "I'm sorry, I'm having trouble processing your request."
    response_message = await message.channel.send(ai_response)
    conversation_context.append({"role": "assistant", "content": ai_response})
    conversations.save_message(conversation_context, message.author.name)

    # Add the button view with thumbs up and thumbs down for message review
    view = ButtonsView()
    await response_message.edit(view=view)


async def channel_mentioned_message(message: discord.Message) -> None:
    """
    Responds to a message in a server channel.

    Args:
        - message (discord.Message): The message object

    Returns:
        None
    """

    if "@everyone" in message.content or "@here" in message.content:
        return

    logger.info(f'[{message.guild.name}][{message.channel.name}][{message.author.name}]: "{message.content}"')
    await message.channel.typing()
    # Discord typing indicator while bot is processing the message
    conversation_context = []
    try:
        if message.type == discord.MessageType.reply:
            conversation_context = await conversations.get_reply_chain(message, 10)
        elif message.channel.type == discord.ChannelType.public_thread:
            conversation_context = await conversations.get_thread_history(message, 10)
        conversation_context.append({"role": "user", "content": message.content})
        logger.debug(f"Conversation context: {conversation_context}")
        ai_response = await conversations.get_response(conversation_context)
    except Exception as e:
        logger.error(f"Error when getting response: {e}")
        ai_response = "I'm sorry, I'm having trouble processing your request."
    await message.reply(ai_response)
    conversation_context.append({"role": "assistant", "content": ai_response})
    conversations.save_message(conversation_context, message.author.name)
