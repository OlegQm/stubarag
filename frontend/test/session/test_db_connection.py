import pytest
import os

"""

A set of unit tests for chat_app session package history_menu module.

"""


def test_Database_initialization():

    from common.session.db_connection import Database

    db = Database()

    assert db.hostname == os.getenv("MONGODB_HOST"), "Failed to set hostname"
    assert db.port == int(os.getenv("MONGODB_PORT")), "Failed to set port"
    assert db.username == os.getenv("MONGODB_USER"), "Failed to set username"
    assert db.password == os.getenv("MONGODB_PASSWORD"), "Failed to set password"
    assert db.name_db == os.getenv("MONGODB_DB"), "Failed to set name_db"
    assert db.name_collection == os.getenv("MONGODB_HISTORY_COLLECTION"), "Failed to set name_collection"

    from pymongo import MongoClient

    assert isinstance(db.client, MongoClient),"Failed to initialize MongoDB client"

    assert db.db == db.client[db.name_db], "Failed to initialize a database inside MongoDB"
    assert db.collection == db.db[db.name_collection], "Failed to initialize a collection inside MongoDB database"


def test_verify_connection():

    from common.session.db_connection import Database

    db = Database()

    assert db.verify_connection() == True, "Verify connection: Failed to verify connection"


def test_set_collection():

    from common.session.db_connection import Database

    db = Database()

    db.set_collection("new_collection","new_database")

    assert db.db == db.client["new_database"]

    assert db.collection == db.db["new_collection"]