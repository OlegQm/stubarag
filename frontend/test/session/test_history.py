import pytest
import random
import streamlit as st

"""

A set of unit tests for chat_app session package history module.

"""

@pytest.fixture(autouse=True)
def mock_session_state_db(initiate_database_client):

    if 'db' not in st.session_state:
        st.session_state.db = initiate_database_client


def cleanup_after_test(rec_id):

    from common.session.db_connection import Database

    db = Database()

    db.collection.delete_one({"_id":rec_id})


#Test for history module 'open_history_stream' function
def test_open_history_stream():

    from bson import ObjectId

    #new_conversation fixture contains call for open_history_stream function
    from src.session.history import open_history_stream

    rec_id = open_history_stream(120414)

    try:
        assert isinstance(rec_id,ObjectId), "Failed to create a new document in MongoDB history collection"

        cleanup_after_test(rec_id)

    except AssertionError as e:
        print(e)


#Test of loading of entire histroical conversation record from database
def test_load_history_document(get_user_history):
    
    document = random.randint(0,2)

    record = get_user_history[document]

    from src.session.history import load_history_document

    retrieved_document = load_history_document(record['_id'])

    try:
        assert retrieved_document == record, "Failed to load history document"

    except AssertionError as e:
        print(e)


#Test of uploading conversation reply to database
def test_append_conversation_reply(get_user_history,initiate_database_client):

    document = random.randint(0,2)

    record = get_user_history[document]

    message = {"role": "user", "content": "I am testing appending to database"}

    from src.session.history import append_conversation_reply

    append_conversation_reply(record['_id'],message)

    db = initiate_database_client

    retrieved_document = db.collection.find_one({"_id":record['_id']})

    try:
        assert retrieved_document["conversation_content"][-1] == message

        db.collection.update_one({'_id':record['_id']},{'$set': {'conversation_content': record["conversation_content"]}})

    except AssertionError as e:
        print(e)


#Test of conversation title updating
def test_update_title(get_user_history,initiate_database_client):

    document = random.randint(0,2)

    record = get_user_history[document]

    from src.session.history import update_title

    update_title(record['_id'])

    db = initiate_database_client

    retrieved_document = db.collection.find_one({"_id":record['_id']})

    try:
        assert "title" in retrieved_document["header"] and (retrieved_document["header"]["title"] is not None and retrieved_document["header"]["title"] != ""),"Title is not being updated"

        db.collection.update_one({"_id":record["_id"]},{'$set': {'header.title': "test title"}})

    except AssertionError as e:
        print(e)


#Test of conversation title retrieving from database
def test_get_title(get_user_history):

    document = random.randint(0,2)

    record = get_user_history[document]

    from src.session.history import get_title

    retrieved_title = get_title(record['_id'])

    try:
        assert retrieved_title == "test title","Failed to get title of conversation from database"
        
    except AssertionError as e:
        print(e)


#Test of conversation history recoding
def test_record_history(get_user_history,initiate_database_client):

    messages = [{"role": "user", "content": "Hello there !"},
                {"role": "assistant", "content": "I can hear you !"}]
    
    document = random.randint(0,2)

    record = get_user_history[document]

    from src.session.history import record_history

    record_history(messages,record['_id'])

    db = initiate_database_client

    retrieved_document = db.collection.find_one({"_id":record['_id']},{"conversation_content":1})
    
    try:
        assert retrieved_document["conversation_content"][-2:] == messages, "History recording is not working properly" 

        db.collection.update_one({'_id':record['_id']},{'$set': {'conversation_content': record["conversation_content"]}})

    except AssertionError as e:
        print(e)


#Test of conversation content retrieving from database
def test_get_conversation_content(get_user_history):
            
    document = random.randint(0,2)

    record = get_user_history[document]

    from src.session.history import get_conversation_content

    retreived_content = get_conversation_content(record['_id'])

    try:
        assert retreived_content == record["conversation_content"], "Failed to load conversation content"

    except AssertionError as e:
        print(e)


#Test of user feedback recording
def test_record_feedback(get_user_history,initiate_database_client):

    document = random.randint(0,2)

    record = get_user_history[document]

    from src.session.history import record_feedback

    record_feedback("good",record['_id'])

    db = initiate_database_client

    result = db.collection.find_one(record['_id'])

    try:
        assert result["conversation_content"][-1]["user_feedback"] == "good","Failed to record user feedback"

        db.collection.update_one({'_id':record['_id']},{'$set': {'conversation_content': record["conversation_content"]}})

    except AssertionError as e:
        print(e)


#Test of conversation summary creation
def test_sumarize(get_user_history):

    document = random.randint(0,2)

    record = get_user_history[document]

    from src.session.history import sumarize

    title = sumarize(record['_id'])

    try:
        assert title is not None and title != "" and len(title) > 0, "Failed to create a summary of conversation"

    except AssertionError as e:
        print(e)


#Test of user history retrieving
def test_get_user_history(get_user_history):

    from src.session.history import get_user_history as get_history

    user_conversations = get_history(120414)

    try:

        assert user_conversations == get_user_history,"Failed to retrieve user history from MongoDB history collection"

    except AssertionError as e:
        print(e)


#Test of history record deletion
def test_delete_record(get_user_history,initiate_database_client):
    
    document = random.randint(0,2)

    record = get_user_history[document]

    from src.session.history import delete_record

    delete_record(record['_id'])

    db = initiate_database_client

    retrieved_document = db.collection.find_one(record['_id'])

    assert retrieved_document == None, "Failed to delete record from database"

    db.collection.insert_one(record)