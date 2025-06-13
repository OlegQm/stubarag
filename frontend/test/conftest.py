import pytest
import random
import os


@pytest.fixture
def mock_streamlit():

    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file("apptest_entrypoint.py",default_timeout=200)
    
    at.run()

    return at


@pytest.fixture
def initiate_database_client():
    
    from common.session.db_connection import Database

    db = Database()

    return db


@pytest.fixture
def get_user_history(initiate_database_client):
    
    db = initiate_database_client

    result = db.collection.find()

    output = [doc for doc in result]

    return output[::-1]


#SUPPORT function which provides a mock history record for database testing purposes
def create_test_record():

    record = {"header":{"user_id":"test@user.sk","date_time":f"{random.randint(0,2024)}-07-03T19:05:22.076+00:00","title":"test title"},
            "conversation_content":[{"role": "user", "content": f"Hello there ! I like number {random.randint(0,100000)}"},
            {"role": "assistant", "content": f"That is very nice ! I like {random.randint(0,100000)}"}]}
    
    return record


#SUPPORT function that inserts test record to the database
def create_user_history():
    
    from common.session.db_connection import Database

    db = Database()

    for i in range(0,3):

        record = create_test_record()
        db.collection.insert_one(record)


#SUPPORT function that delete all records representing user history
def user_history_cleanup():

    from common.session.db_connection import Database

    db = Database()

    db.collection.drop()


@pytest.hookimpl()
def pytest_sessionstart(session):
    """ Code to run once before any tests are executed """

    os.environ['MONGODB_HISTORY_COLLECTION'] = "test"

    create_user_history()


@pytest.hookimpl()
def pytest_sessionfinish(session, exitstatus):
    """ Code to run once after all tests are executed """

    user_history_cleanup()
