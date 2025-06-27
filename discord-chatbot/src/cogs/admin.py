import discord
import os
from dotenv import load_dotenv

from src.utils.news_scraper import save_news_record, is_message_stored
from common.logging.global_logger import logger

load_dotenv()
FEI_NEWS_SERVER = os.getenv('FEI_NEWS_SERVER')
FEI_NEWS_CHANNEL = os.getenv('FEI_NEWS_CHANNEL')
FEI_NEWS_AUTHOR = os.getenv('FEI_NEWS_AUTHOR')

async def news_message(message: discord.Message) -> None:
    """
    Saves the news message to the database.
    
    Args:
        - message (discord.Message): The message object

    Returns:
        None
    """
    logger.info(f'[NEWS][{message.author.name}]: "{message.content}"')
    logger.info(f"Expected author: {FEI_NEWS_AUTHOR}")
    # if message.author.name != FEI_NEWS_AUTHOR:
    #     logger.warning(f"News message author is not {FEI_NEWS_AUTHOR}. Ignoring message.")
    #     return
    await save_news_record(message)


async def news_update(channels: list) -> None:
    """
    Updates the news channel with the latest messages.

    Args:
        - channels (list): List of channels to check for news messages

    Returns:
        None
    """
    channel = discord.utils.get(channels, guild__name=FEI_NEWS_SERVER, name=FEI_NEWS_CHANNEL)
    logger.info(f"Updating news from channel: {channel.guild.name}/{channel.name}")
    if channel:
        async for channel_message in channel.history(limit=10):
            if not await is_message_stored(channel_message):
                await save_news_record(channel_message)
                logger.info(f"Saved news message: {channel_message.content}")
    else:
        logger.error(f"Channel not found. Guild:s: {FEI_NEWS_SERVER}, Channel: {FEI_NEWS_CHANNEL}")
    