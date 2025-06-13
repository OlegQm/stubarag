from pydantic_settings import BaseSettings

"""

This module defines the configuration settings for the application using Pydantic's BaseSettings.

"""


class Settings(BaseSettings):
    """
    Settings class for application configuration.
    This class inherits from BaseSettings and is used to manage application
    configuration through environment variables. The configuration includes
    API keys, model names, and database connection details.

    Attributes:
        openai_api_key (str): API key for OpenAI services.
        embedding_model (str): Name of the embedding model to be used.
        dev_user (str): Developer user identifier.
        chroma_host (str): Host address for Chroma service.
        chroma_port (int): Port number for Chroma service.
        chroma_collection_name (str): Collection name for Chroma service.
        mongodb_host (str): Host address for MongoDB.
        mongodb_port (int): Port number for MongoDB.
        mongodb_user (str): Username for MongoDB authentication.
        mongodb_password (str): Password for MongoDB authentication.
        mongodb_db (str): Database name in MongoDB.
        mongodb_history_collection (str): Collection name for storing history in MongoDB.

    Config:
        env_file (str): Path to the environment file containing configuration variables.

    """

    openai_api_key: str
    embedding_model: str
    dev_user: str
    chroma_host: str
    chroma_port: int
    chroma_collection_name: str
    mongodb_host: str
    mongodb_port: int
    mongodb_user: str
    mongodb_password: str
    mongodb_db: str
    mongodb_history_collection: str

    class Config:
        env_file = ".env"


settings = Settings()
