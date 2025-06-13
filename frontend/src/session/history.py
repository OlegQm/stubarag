import datetime

import streamlit as st
from bson import ObjectId
from src.session import handlers

from common.llm.title_flow import conversation_title_agent
from common.session.db_connection import mongo_db
from common.session.exceptions import DocumentNotFound

"""

A module for handling the communication between conversation DB and frontend chat app.

!!! WILL BE REPLACED WITH API CALLS TO THE MONGODB CONTAINER IN THE FUTURE !!!

"""


# Function that initialize session history recording
# Returns ObjectID of MongoDB document of started conversation
def open_history_stream(user_id: str) -> ObjectId:
    """
    Opens a conversation history recording stream for a given user by creating a new document in the MongoDB collection.

    Args:
        - user_id (str): The unique identifier of the user.

    Returns:
        - ObjectId (instance of ObjectId() class): The ID of the inserted document.

    """

    # Get current date and time for record timestamp
    now = datetime.datetime.now()
    date_time = now.strftime("%d-%m-%Y_%H-%M-%S")

    # Create a new document in the MongoDB collection
    update = {
        "header": {
            "date_time": date_time,
            "user_id": user_id,
            "ingested": False,
            "discord": False,
            "feedback": None,
            "review": None,
        }
    }

    # Insert the document into the MongoDB collection
    document = mongo_db.collection.insert_one(update)

    # Return the ObjectId() of the inserted document
    return document.inserted_id


# Function that load content of current conversation history record
def load_history_document(rec_id: ObjectId) -> dict:
    """
    Loads a history document from the MongoDB collection using the provided record ID.

    Args:
        - rec_id (ObjectId): The record ID of the history document to be retrieved.

    Returns:
        - history_data (dict): The history document if found, otherwise None.

    Raises:
        - DocumentNotFound: If the history document with the given record ID does not exist.

    """

    try:

        # Find the history document with the provided record ID in the MongoDB collection
        history_data = mongo_db.collection.find_one({"_id": rec_id})

        # If the history document does not exist, raise a DocumentNotFound exception
        if history_data is None:
            raise DocumentNotFound

        # Return the history document (can be handled like python dictionary - its json-like structure)
        return history_data

    except DocumentNotFound:

        print(
            f"[{handlers.timestamp()} : {__name__} - {load_history_document.__name__}] Requested history record does not exist: {rec_id}"
        )
        return None


# Function that appends given message to the historical record 'conversation_content' field
def append_conversation_reply(rec_id: ObjectId, message: dict) -> None:
    """
    Appends given message to the historical record 'conversation_content' field.

    Args:
        - rec_id (ObjectId): The unique identifier of the record to update.
        - message (dict): The message to append to the conversation content.

    Returns:
        None

    """

    # Define the filter to find the document with the provided record ID
    filter = {"_id": rec_id}

    # Define operation to append the message to the
    # 'conversation_content' key in history record
    update = {"$push": {"conversation_content": message}}

    # Update the document in the MongoDB collection
    mongo_db.collection.update_one(filter, update)


# Function that updates conversation title
def update_title(rec_id: ObjectId) -> None:
    """
    Updates the title of a conversation record in the MongoDB collection.

    Args:
        - rec_id (instance of ObjectId() class): The unique identifier of the record to update.

    Returns:
        None

    """

    # Get the title of the conversation
    title = sumarize(rec_id)

    # Define the filter to find the document with the provided record ID
    filter = {"_id": rec_id}

    # Define the operation to update the 'title' value in the 'header' key
    # of the history record
    update = {"$set": {"header.title": title}}

    # Update the document in the MongoDB collection
    mongo_db.collection.update_one(filter, update)


# Function that returns title of conversation from conversation history record
#'Nový chat' is default option if title is not present
def get_title(rec_id: ObjectId) -> str:
    """
    Retrieve the title of conversation from conversation history record.

    'Nový chat' is default option if title is not present

    Args:
        - rec_id (ObjectId): The unique identifier of the conversation record.

    Returns:
        - str: The title of the chat session if it exists, otherwise "Nový chat".

    """

    # Define the filter to find the document with the provided record ID
    filter = {"_id": rec_id}

    # Find the document and retrieve only the 'header.title' value
    result = mongo_db.collection.find_one(filter, {"header.title": 1})

    # Return the title of the conversation if it exists, otherwise "Nový chat"
    if "title" in result["header"]:
        return result["header"]["title"]
    else:
        return "Nový chat"


# Function that write last two conversation replies to history file
# Last prompt and LLM answer is processed
def record_history(messages: list, rec_id: ObjectId) -> None:
    """
    Records the conversation history by appending user prompts and LLM responses to a record in MongoDB history collection.

    Args:
        - messages (list): A list of messages in the conversation. The last two messages are considered for recording.
        - rec_id (ObjectId): The unique identifier for the conversation record.

    Returns:
        None

    Notes:
        - If the length of messages is greater than 1, the function appends the user prompt and LLM response to the conversation record.
        - If the length of messages is a multiple of 6 or exactly 2, the function updates the title of the conversation record.

    """

    if len(messages) > 1:

        # Append user prompt:
        append_conversation_reply(rec_id, messages[len(messages) - 2])
        # Append LLM response:
        append_conversation_reply(rec_id, messages[len(messages) - 1])

        # Update title of conversation record if conditions are met
        # if len(messages) % 6 == 0 or len(messages) == 2:
        #     update_title(rec_id)
        update_title(rec_id)


# Function that returns an array with content of conversation with 'rec_id' ObjectID
def get_conversation_content(rec_id: ObjectId) -> list[dict]:
    """
    Retrieve the conversation content from the conversation record with given record ID.

    Args:
        - rec_id (ObjectId): The unique identifier of the record to retrieve.

    Returns:
        - list: The conversation content associated with the given record ID.

    """

    # Define the filter to find the document with the provided record ID
    filter = {"_id": rec_id}

    # Find the document and retrieve only the 'conversation_content' array
    result = mongo_db.collection.find_one(filter, {"conversation_content": 1})

    # Return the 'conversation_content' array from the result
    return result["conversation_content"]


# Callback function for feedback buttons. Also regulate the feedback states fo current session.
def record_feedback(feedback: str, rec_id: ObjectId) -> None:
    """
    Callback function for feedback buttons.

    Also regulate the feedback states fo current session.
    Records user feedback for a specific conversation record.
    This function updates the last element of the 'content' array in the
    conversation document identified by `rec_id` with the provided `feedback`.
    It also updates the session state to reflect the feedback submission.

    Args:
        - feedback (str): The feedback provided by the user. Expected values are "good" or "bad".
        - rec_id (ObjectId): The unique identifier of the conversation record in the database.

    Returns:
        None

    Influenced Session State Variables:
        - st.session_state.good_emphasis
        - st.session_state.bad_emphasis
        - st.session_state.feedback_submited_good
        - st.session_state.feedback_submited_bad

    """

    # Define the filter to find the document with the provided record ID
    filter = {"_id": rec_id}

    # Find the document and retrieve the 'content' array
    conversation_content = get_conversation_content(rec_id)

    # Determine the index of the last element in the 'content' array
    last_index = len(conversation_content) - 1

    # Define the update operation to add a new key-value pair to the last element in 'content'
    update = {"$set": {f"conversation_content.{last_index}.user_feedback": feedback}}

    # Update the document in the MongoDB history collection
    mongo_db.collection.update_one(filter, update)

    # Update feedback for entire conversation in header
    update = {"$set": {"header.feedback": feedback}}
    mongo_db.collection.update_one(filter, update)


# Function that create title for conversation
def sumarize(rec_id: ObjectId) -> str:
    """
    Summarizes the conversation content for a given record ID and creates a title for conversation.

    Args:
        - rec_id (instance of ObjectId() class): The record ID of the conversation to summarize.

    Returns:
        - str: A summary title for the conversation content.

    """

    # Get the conversation content from the MongoDB collection
    conversation_content = get_conversation_content(rec_id)

    # Generate a title for the conversation using the LLM model
    # Auxiliary LLM model is used for title generation
    summary = conversation_title_agent(str(conversation_content))
    # Return the generated title
    return summary


# Function that returns a list of user historical conversations from MongoDB history collection
def get_user_history(user_id: str) -> list[ObjectId]:
    """
    Retrieve the conversation history for a given user.

    Args:
        - user_id (str): The unique identifier of the user.

    Returns:
        - list: A list of conversation IDs associated with the user, in reverse chronological order.

    """

    # Define the filter to find the documents with the provided user ID
    filter = {"header.user_id": user_id}

    # Find the documents in the MongoDB collection and retrieve only the '_id' values
    results = mongo_db.collection.find(filter, {"_id": 1})

    # Reverse order of the conversation IDs to match the chronological order
    # Newest conversation is at the top of the list
    user_conversations = [document["_id"] for document in results]

    # Return the list of conversation IDs
    return user_conversations[::-1]


# Function that delete a record with ObjectID 'rec_id' from MongoDB history collection
def delete_record(rec_id: ObjectId) -> None:
    """
    Deletes a record from the MongoDB collection based on the provided record ID.

    Args:
        - rec_id (ObjectId): The ID of the record to be deleted.

    Returns:
        None

    """

    # Define the filter to find the document with the provided record ID
    filter = {"_id": rec_id}

    # Delete the document from the MongoDB collection
    mongo_db.collection.delete_one(filter)
