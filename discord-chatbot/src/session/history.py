import datetime
from bson import ObjectId

from common.session.db_connection import mongo_db
from common.llm.title_flow import conversation_title_agent
from common.logging.global_logger import logger


def save_conversation(messages: list, user_id: str) -> ObjectId:
    """
    Saves a conversation record to the MongoDB collection.

    Args:
        - conversation (list): The conversation content to save
        - user_id (str): The user ID associated with the conversation

    Returns:
        - ObjectId: The ID of the conversation record stored in the MongoDB collection

    """
    record = create_conversation_record(messages, user_id)

    mongo_db.set_collection("history")
    try:
        return mongo_db.collection.insert_one(record)
    except ConnectionError as e:
        logger.error(e)
        return None


# Returns standardized file record based on template to be stored in MongoDB
def create_conversation_record(messages: list, user_id: str) -> dict:
    """
    Creates a standardized file record based on a template to be stored in the MongoDB collection.

    Args:
        - messages (list): The conversation content to save.
        - user_id (str): The user ID associated with the conversation.

    Returns:
        - dict: The file record to be stored in the MongoDB collection.

    """

    now = datetime.datetime.now()
    date_time = now.strftime("%d-%m-%Y_%H-%M-%S")

    # Teplate record
    record = {
        "header": {
            "date_time": date_time,
            "user_id": user_id,
            "ingested": False,
            "discord": True,
            "feedback": None,
            "review": None,
            "title": conversation_title_agent(str(messages)),
        },
        "conversation_content": messages,
    }

    return record
