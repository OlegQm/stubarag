"""
This module defines the Pydantic models used for API responses in the application.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel

class IngestResponse(BaseModel):
    """
    IngestResponse is a Pydantic model representing the
    response schema for an ingestion operation.

    Attributes:
        message (str): A message indicating the status or result of the ingestion.
        metadatas (dict): A dictionary containing metadata related to the ingestion.

    """

    message: str
    metadatas: dict


class Metadata(BaseModel):
    """
    A class used to represent Metadata.

    Attributes:
        date (str): The date associated with the metadata.
        filename (str): The name of the file associated with the metadata.
        user (str):The user associated with the metadata.

    """

    date: str
    filename: str
    user: str


class DocumentResponse(BaseModel):
    """
    DocumentResponse represents the response structure for a document.

    Attributes:
        content (str): The content of the document.
        metadata (Metadata): Metadata associated with the document.

    """

    content: str
    metadata: Metadata


class QueryResponse(BaseModel):
    """
    QueryResponse is a Pydantic model that represents the response structure for a query.

    Attributes:
        documents (list[DocumentResponse]): A list of DocumentResponse objects
        representing the documents returned by the query.

    """

    documents: List[DocumentResponse]


class DeleteResponse(BaseModel):
    """
    DeleteResponse is a Pydantic model used to represent the response message
    for a delete operation.

    Attributes:
        message (str): A message indicating the result of the delete operation.

    """

    message: str

class RandomQuestion(BaseModel):
    """
    Schema representing a single random question.

    Attributes:
        question (str): The text of the question.
        answer (str): The text of the answer.
        no (int): The sequential number of the question.
        doc (Optional[str]): The document associated with the question, if any.
        url (Optional[str]): The URL for additional context or source, if any.
    """
    question: str
    answer: str
    no: int
    doc: str
    url: str

class RandomQuestionResponse(BaseModel):
    """
    Schema representing the overall response for random questions.

    Attributes:
        result (Union[List[RandomQuestion], None]): A list of random questions
            or None if no result is available.
        message (str): A descriptive message about the response.
        status (str): The status of the response, e.g., "success" or "error".
    """
    result: List[RandomQuestion]
    message: str
    status: int

class SimilarQuestion(BaseModel):
    """
    Represents a single similar question retrieved from a collection.

    Attributes:
        question (str): The text of the similar question.
        answer (str): The corresponding answer to the question.
        no (int): The identifier or sequential number of the question in the collection.
        doc (str): The name of the document associated with the question.
        url (str): The URL linking to additional resources or the document.
    """
    question: str
    answer: str
    no: int
    doc: str
    url: str

class SimilarQuestionResponse(BaseModel):
    """
    Represents the response for a query to retrieve similar questions.

    Attributes:
        result (List[SimilarQuestion]): A list of similar questions meeting the query criteria.
            message (str): A descriptive message about the operation (e.g., success or error details).
        status (int): The HTTP status code representing the operation's outcome.
    """
    result: List[SimilarQuestion]
    message: str
    status: int

class DeleteRecordResponse(BaseModel):
    """
    Response model for deleting a one record from the collection in ChromaDB.
    
    Attributes:
        message (str): A descriptive message about the outcome
            of the delete operation.
        result (int): The number of records that were deleted.
    """
    message: str
    status: int

class ClearCollectionResponse(BaseModel):
    """
    ClearCollectionResponse represents the response model
    for the collection clearing operation.

    This class is used to return the result of the FAQ endpoint
    that clears a collection in the database.

    Attributes:
        message (str): A description of the operation result,
            e.g., a message indicating successful clearing.
        status (int): The status code of the operation:
            - 200: The operation was successfully completed.
            - 500: An error occurred during the operation.
    """
    message: str
    status: int

class LoadFaqDataResponse(BaseModel):
    """
    LoadFaqDataResponse represents the response
        model for the FAQ data loading operation.

    This class is used to return the result of the
    endpoint that loads FAQ data into the database.

    Attributes:
        message (str): A description of the operation result,
            such as a success message or error details.
        status (int): The status code of the operation:
                      - 200: The FAQ data was successfully loaded.
                      - 500: An internal error occurred during the operation.
    """
    message: str
    status: int

class WebScraperResponse(BaseModel):
    """
    Represents the response for a web scraping operation.

    Attributes:
        status (str): The status of the operation (e.g., success or error).
        data (str): webpage content or error message.
    """
    status: int
    data: str

class Page(BaseModel):
    """
    Represents a webpage with its URL, description, and owner.

    Attributes:
        url (str): The URL of the webpage.
        description (Optional[str]): A brief description of the webpage. Defaults to "Brief description of the webpage."
        owner (Optional[str]): The owner of the webpage. Defaults to "FEI STU."
    """
    url: str
    description: Optional[str] = "Brief description of the webpage."
    owner: Optional[str] = "FEI STU"

class ChunkMetedata(BaseModel):
    """
    Represents metadata for a specific chunk of text.

    Attributes:
        url (str): The URL of the source document.
        description (str): A brief description of the page's content.
        md5 (str): The MD5 hash of the entire page.
        date (str): The date associated with the page.
        owner (str): The owner or author of the page.
        chunk_number (int): The sequential number of the chunk in the page.
        chunk_md5 (str): The MD5 hash of the specific chunk.
    """
    url: str
    description: str
    md5: str
    date: str
    owner: str
    chunk_number: int
    chunk_md5: str

class Chunk(BaseModel):
    """
    Represents a chunk of a document along with its metadata.

    Attributes:
        document (str): The content of the chunk.
        metadata (ChunkMetedata): Metadata related to the chunk.
    """
    document: str
    metadata: ChunkMetedata

class Chunks(BaseModel):
    """
    Represents a collection of chunks from a document.

    Attributes:
        chunks (List[Chunk]): A list of Chunk objects representing parts of a document.
    """
    chunks: List[Chunk]

class RefreshPagesContentRespose(BaseModel):
    """
    Represents the response format for the refresh pages operation.

    Attributes:
        status (int): The HTTP status code of the response.
        message (str): A message describing the result of the operation.
    """
    status: int
    message: str

class TestsResponse(BaseModel):
    """
    TestsResponse is a model representing the response structure for test results.

    Attributes:
        custom_results (List[Dict[str, str]]): A list of dictionaries where each dictionary contains
            information about whether a question passed the 95% threshold.
        pytest_log (str): A string containing the name of the test and whether it passed.
    """
    message: str
    status: int
    custom_results: List[Dict[str, str]]
    pytest_log: str

class UploadQNAResponse(BaseModel):
    """
    Represents the response for uploading questions and answers to MongoDB.

    Attributes:
        status (int): The status code indicating the result of the upload operation.
        message (str): A message providing additional details about the upload status.
    """
    status: int
    message: str

class DropCollectionResponse(BaseModel):
    """
    Represents the response for dropping a collection in ChromaDB and MongoDB.

    Attributes:
        message (str): A message indicating the result of the drop operation.
        status (int): The status code indicating the result of the drop operation.
    """
    message: str
    status: int
