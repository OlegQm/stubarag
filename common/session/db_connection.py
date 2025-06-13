import os

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

"""

This module contains the Database class for MongoDB connection and operations.

"""


class Database:
    """
    A class representing a set up and ready to use MongoDB database.

    Attributes:
        - client (pymongo.MongoClient): The MongoDB client object.
        - db (pymongo.database.Database): The MongoDB database object.
        - collection (pymongo.collection.Collection): The MongoDB collection object.

    Methods:
        - __init__(): Initializes the Database object with the provided parameters.
        - verify_connection(): Verifies the connection to MongoDB and tries reconnecting if the connection is lost.
        - set_collection(new_collection, new_database=None): Sets the collection in the database.

    """

    def __init__(
        self,
        hostname: str = None,
        port: int = None,
        username: str = None,
        password: str = None,
        name_db: str = None,
        name_collection: str = None,
    ) -> None:
        """
        Initialize the database connection parameters and create a MongoDB client.

        Args:
            - hostname (str, optional): The hostname of the MongoDB server. Defaults to the value of the "MONGODB_HOST" environment variable.
            - port (int, optional): The port number of the MongoDB server. Defaults to the value of the "MONGODB_PORT" environment variable.
            - username (str, optional): The username for authentication. Defaults to the value of the "MONGODB_USER" environment variable.
            - password (str, optional): The password for authentication. Defaults to the value of the "MONGODB_PASSWORD" environment variable.
            - name_db (str, optional): The name of the database. Defaults to the value of the "MONGODB_DB" environment variable.
            - name_collection (str, optional): The name of the collection. Defaults to the value of the "MONGODB_HISTORY_COLLECTION" environment variable.

        Returns:
            None

        """
        # Set the database connection parameters
        self.hostname = hostname or os.getenv("MONGODB_HOST")
        self.port = port or int(os.getenv("MONGODB_PORT"))
        self.username = username or os.getenv("MONGODB_USER")
        self.password = password or os.getenv("MONGODB_PASSWORD")
        self.name_db = name_db or os.getenv("MONGODB_DB")
        self.name_collection = name_collection or os.getenv(
            "MONGODB_HISTORY_COLLECTION"
        )

        # Create a MongoDB client
        self.client = MongoClient(
            self.hostname, self.port, username=self.username, password=self.password
        )
        self.db = self.client[self.name_db]
        self.collection = self.db[self.name_collection]

    # Verifies connection to MongoDB server
    def verify_connection(self) -> bool:
        """
        Verifies the connection to the MongoDB server.

        If connection is invalid, tries reconnecting.

        Args:
            None

        Returns:
            bool: True if the connection is successful, False otherwise.

        Raises:
            ConnectionFailure: If the connection to the MongoDB server fails.

        """
        try:
            # Try to ping the MongoDB
            self.client.admin.command("ping")

            return True
        # If the connection fails, try to reconnect
        except ConnectionFailure:
            print("Connection lost, reconnecting...")
            try:
                # Try to establish a new connection
                self.client = MongoClient(
                    self.hostname,
                    self.port,
                    username=self.username,
                    password=self.password,
                )

                return True
            # If the second attempt at the connection fails, return False
            except ConnectionFailure:
                print("Connection to MongoDB failed")

                return False

    # Sets collection in DB (default option is for conversation history)
    def set_collection(self, new_collection: str, new_database: str = None) -> None:
        """
        Sets the collection to be used for database operations.

        Args:
            - new_collection (str): The name of the new collection.
            - new_database (str, optional): The name of the new database. If not provided, the current database will be used.

        Returns:
            None

        """

        # If new_database is not provided, use the current database
        if new_database is None:
            new_database = self.name_db

        # Set the new collection
        self.db = self.client[new_database]
        self.collection = self.db[new_collection]

    def __query_validator():
        pass


# Create a Database object for history module
mongo_db = Database()
