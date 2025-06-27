from app.config import settings
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from pymongo.collection import Collection

from chromadb import AsyncHttpClient


"""

This module provides functionality to connect to a MongoDB database and to create an asynchronous HTTP client for ChromaDB.

Global variables:
    MONGODB_HOST (str): MongoDB host address from settings.
    MONGODB_PORT (int): MongoDB port number from settings.
    MONGODB_USER (str): MongoDB username from settings.
    MONGODB_PASS (str): MongoDB password from settings.
    MONGODB_DB (str): MongoDB database name from settings.
    MONGODB_HISTORY_COLLECTION (str): MongoDB collection name from settings.
    CHROMA_HOST (str): ChromaDB host address from settings.
    CHROMA_PORT (int): ChromaDB port number from settings.
    mongo_db (MongoDB): An instance of the MongoDB class initialized with settings values.

"""

MONGODB_HOST = settings.mongodb_host
MONGODB_PORT = settings.mongodb_port
MONGODB_USER = settings.mongodb_user
MONGODB_PASS = settings.mongodb_password
MONGODB_DB = settings.mongodb_db
MONGODB_HISTORY_COLLECTION = settings.mongodb_history_collection
CHROMA_HOST = settings.chroma_host
CHROMA_PORT = settings.chroma_port


class MongoDB:
    """
    A class to manage connections and operations with a MongoDB database.

    Attributes:
        host (str): The hostname or IP address of the MongoDB server.
        port (int): The port number on which the MongoDB server is listening.
        username (str): The username for authenticating with the MongoDB server.
        password (str): The password for authenticating with the MongoDB server.
        db_name (str): The name of the database to connect to.
        collection_name (str): The name of the collection to interact with.
        client (MongoClient): The MongoClient instance for connecting to the MongoDB server.
        db (Database): The Database instance for the specified database.
        collection (Collection): The Collection instance for the specified collection.

    Methods:
        __init__(host: str, port: int, username: str, password: str, db_name: str, collection_name: str):
            Initializes the MongoDB connection with the provided parameters and connects to the database.
        _connect():
            Establishes a connection to the MongoDB server and initializes the database and collection attributes.
        get_collection() -> Collection:
            Returns the collection instance for the specified collection.
        verify_connection() -> bool:
            Verifies the connection to the MongoDB server by pinging it. Attempts to reconnect if the connection is lost.

    """

    def __init__(self, host: str, port: int, username: str, password: str, db_name: str, collection_name: str):
        """
        Initializes the database connection parameters and establishes a connection.

        Args:
            host (str): The hostname of the database server.
            port (int): The port number on which the database server is listening.
            username (str): The username for authenticating with the database.
            password (str): The password for authenticating with the database.
            db_name (str): The name of the database to connect to.
            collection_name (str): The name of the collection within the database.

        """

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
        self._connect()

    def _connect(self):
        """
        Establishes a connection to the MongoDB database.
        This method attempts to create a connection to the MongoDB server using the
        provided host, port, username, and password. It initializes the client, 
        database, and collection attributes of the instance. If the connection 
        fails, it catches the ConnectionFailure exception and prints an error message.

        """

        try:
            self.client = MongoClient(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
            )
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
        except ConnectionFailure:
            print("Initial connection to MongoDB failed")

    def get_collection(self) -> Collection:
        """
        Retrieve the collection instance.

        Returns:
            Collection: The collection instance.

        """

        return self.collection
    
    def get_collection_by_name(
        self,
        collection_name: str,
    ) -> Collection:
        if collection_name in self.db.list_collection_names():
            return self.db[collection_name]
        return None

    def get_or_create_collection(
        self,
        collection_name: str,
        *index_fields: tuple,
        unique: bool = False
    ) -> Collection:
        """
        Retrieves an existing collection or creates a new one if it does not exist, with the specified indexes.

        Args:
            collection_name: The name of the collection.
            index_fields: Pairs of (field_name, order), e.g., ("url", pymongo.ASCENDING).
            unique: Indicates whether the index should be unique.

        Returns:
            Collection: The MongoDB collection object.
        """
        collection = self.get_collection_by_name(collection_name)
        if collection is None:
            self.db.create_collection(collection_name)
            collection = self.db[collection_name]

        if index_fields:
            collection.create_index(list(index_fields), unique=unique)

        return collection

    def list_collection_names(self):
        """
        Retrieve a list of all collection names in the connected database.

        Returns:
            list: A list of collection names.
        """
        if self.db is not None:
            return self.db.list_collection_names()
        else:
            print("Database connection not initialized.")
            return []

    def verify_connection(self) -> bool:
        """
        Verifies the connection to the MongoDB server.

        Returns:
            bool: True if the connection is successful, False otherwise.

        """

        try:
            # Try to ping the MongoDB
            self.client.admin.command("ping")
            return True
        except ConnectionFailure:
            print("Connection lost, reconnecting...")
            try:
                # Try to establish a new connection
                self._connect()
                return True
            except ConnectionFailure:
                print("Connection to MongoDB failed")
                return False


mongo_db = MongoDB(
    host=settings.mongodb_host,
    port=settings.mongodb_port,
    username=settings.mongodb_user,
    password=settings.mongodb_password,
    db_name=settings.mongodb_db,
    collection_name=settings.mongodb_history_collection
)


async def get_chromadb_client():
    """
    Asynchronously creates and yields a ChromaDB client.

    Yields:
        AsyncHttpClient: An instance of the ChromaDB client.

    """
 
    chroma_client = await AsyncHttpClient(
        host=CHROMA_HOST,
        port=CHROMA_PORT
    )
    yield chroma_client
