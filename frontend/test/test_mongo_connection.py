import pytest
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

#testing connection to the REAL MongoDB of chat_app

#ONLY working when used with docker compose

def test_real_time_connection():
    
    from common.session import db_connection

    database = db_connection.Database()

    try:
        database.verify_connection()

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        pytest.fail(f"Failed to connect to the MongoDB container: {e}")