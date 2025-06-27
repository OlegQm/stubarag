import discord
import datetime
from bson import ObjectId
import os
from dotenv import load_dotenv


from common.logging.global_logger import logger
from common.session.db_connection import mongo_db
from common.llm.title_flow import conversation_title_agent


async def create_news_record(message: discord.Message) -> dict:
    """
    Creates a news record from a Discord message.

    Args:
        - message (discord.Message): The message object to create a record from

    Returns:
        - dict: The news record created from the message
    """
    now = datetime.datetime.now()
    date_time = now.strftime("%d-%m-%Y_%H-%M-%S")
    try:
        id = message.id
        author = message.author.name
        content = message.content
        logger.info(message.attachments[0].content_type)
        if message.attachments and "image/" in message.attachments[0].content_type:
            image = await message.attachments[0].read()
        else:
            image = None
    except Exception as e:
        logger.error(e)
        return None
    # Template record
    record = {
        "message_id": id,
        "date_time": date_time,
        "author": author,
        "title": conversation_title_agent(str(content)),
        "content": content,
        "image": image
    }
    return record


async def save_news_record(message: discord.Message) -> ObjectId:
    """
    Saves a news record to the MongoDB collection.

    Args:
        - message (discord.Message): The message object to save

    Returns:
        - ObjectId: The ID of the news record stored in the MongoDB collection
    """
    record = await create_news_record(message)
    mongo_db.set_collection("student_news")
    try:
        author = record["author"]
        content = record["content"]
        logger.info(f"Saving news record: {author}: {content}")
        return mongo_db.collection.insert_one(record)
    except ConnectionError as e:
        logger.error(e)
        return None
    

async def is_message_stored(message: discord.Message) -> bool:
    """
    Checks if a message is already stored in the MongoDB collection.

    Args:
        - message (discord.Message): The message object to check

    Returns:
        - bool: True if the message is already stored, False otherwise
    """
    
    mongo_db.set_collection("student_news")
    try:
        result = mongo_db.collection.find_one({"message_id": message.id})
        return result is not None
    except ConnectionError as e:
        logger.error(e)
        return False
