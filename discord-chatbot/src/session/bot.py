import discord
import os
from dotenv import load_dotenv
from discord import app_commands

from src.cogs import admin, commands, general
from src.utils import conversations
from common.logging.global_logger import logger


# Load the token from the .env file and set up the client as globlal variable
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
FEI_NEWS_SERVER = os.getenv('FEI_NEWS_SERVER')
FEI_NEWS_CHANNEL = os.getenv('FEI_NEWS_CHANNEL')
FEI_NEWS_AUTHOR = os.getenv('FEI_NEWS_AUTHOR')
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


def run_bot() -> None:
    """
    Entry point for the Discord bot. TOKEN is loaded from the .env file.

    Args:
        None

    Returns:
        None
    """
        
    try:
        client.run(TOKEN)
    except Exception as e:
        logger.error(f"Error when starting Discord bot: {e}")


@client.event
async def on_ready() -> None:
    """
    Checks if the bot started correctly. Logs server names where it's online.

    Args:
        None

    Returns:
        None
    """

    try:
        await tree.sync()
        logger.info(f'{client.user} is now running on servers: {[guild.name for guild in client.guilds]}.')
        await admin.news_update(client.get_all_channels())
    except Exception as e:
        logger.error(f"Error when syncing Discord bot: {e}")


@client.event
async def on_error(event: any, *args, **kwargs) -> None:
    """
    Called when an error is raised.

    Args:
        - event (any): The event that caused the error
        - args (list): The arguments of the event
        - kwargs (dict): The keyword arguments of the event

    Returns:
        None
    """
    logger.error("Fatal error")
    message = args[0] # Message object that caused the error
    logger.exception(f"Error in {event}")
    await message.channel.send("Rozbil som sa! :(", delete_after=10)


@client.event
async def on_message(message: discord.Message) -> None:
    """
    Called on message event. Chooses the bot's response to a message.

    Args:
        message (discord.Message): The message object

    Returns:
        None
    """
    # don't respond to ourselves
    if message.author == client.user:
        return
    # respond to private messages in DM
    if message.channel.type == discord.ChannelType.private:
        await general.private_message(message, client)
    # news message
    elif message.guild.name == FEI_NEWS_SERVER and message.channel.name == FEI_NEWS_CHANNEL:
        await admin.news_message(message)
    # respond to messages in a server channel
    else:
        # if the bot is mentioned or message is reply to bot, reply in channel
        if client.user.mentioned_in(message) or await conversations.is_reply_to_bot(client, message):
            await general.channel_mentioned_message(message)


@tree.command(name="help")
async def help(interaction: discord.Interaction) -> None:
    """
    Sends a help message to the user.

    Args:
        - interaction (discord.Interation): The interaction object (slash cmd)

    Returns:
        None
    """ 

    await commands.help_command(interaction)


@tree.command(name="msg")
@app_commands.describe(question="Ask me anything about FEI STU and I'll DM you!")
async def msg(interaction: discord.Interaction, question: str) -> None:
    """
    DMs the user with a response to question.

    Args:
        - interaction (discord.Interation): The interaction object (slash cmd)
        - question (str): User prmpmt for the bot

    Returns:
        None
    """ 

    await commands.msg_command(interaction, question)