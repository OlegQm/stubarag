"""
This module provides functionality to extract static text content from web pages,
store the extracted data in a MongoDB collection, and manage a vector database 
for embedding and querying the data. It includes helper functions to handle 
responses, calculate MD5 hashes, and interact with MongoDB and ChromaDB.
"""
import datetime
import hashlib
import requests
import re
import uuid
import logging

import pymongo
from pymongo.collection import Collection as MongoCollection
from markdownify import markdownify as md
from fastapi import status
from fastapi.responses import JSONResponse
from bs4 import BeautifulSoup, Comment

from app.routers.schemas import WebScraperResponse
from app.database import mongo_db, get_chromadb_client
from app.utils import initialize_embedding_function

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)

def clean_text(text: str) -> str:
    """
    Cleans the input text by performing the following operations:
    1. Removes control characters (ASCII codes 0-31 and 127).
    2. Replaces multiple whitespace characters with a single space.
    3. Strips leading and trailing whitespace.
    4. Replaces multiple spaces or tabs with a single space.
    5. Replaces multiple newline characters with a single newline.

    Args:
        text (str): The input text to be cleaned.

    Returns:
        str: The cleaned text.
    """
    text = re.sub(r'[\x00-\x1F\x7F]', '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def split_text_into_chunks(text: str, chunk_size: int = 1000) -> list:
    """
    Splits the text into chunks for model processing without breaking words or sentences.
    
    Args:
        text (str): The input text.
        chunk_size (int): The maximum length of each chunk in characters.

    Returns:
        list: A list of text chunks.
    """
    if not text.strip():
        raise ValueError("Text must be a non-empty string.")
    if not chunk_size > 0:
        raise ValueError("Chunk size must be a positive integer.")
    chunks = []
    while text:
        if len(text) <= chunk_size:
            chunks.append(text.strip())
            break
        split_point = text[:chunk_size].rfind('. ')
        if split_point == -1 or split_point < 0.75 * chunk_size:
            split_point = text[:chunk_size].rfind(' ')
        if split_point == -1 or split_point < 0.75 * chunk_size:
            split_point = chunk_size
        chunks.append(text[:split_point + 1].strip())
        text = text[split_point + 1:].strip()
    return chunks


def return_response_in_scrapper_format(status: int, data: str) -> JSONResponse:
    """
    Formats and returns a JSONResponse with the specified status and data.

    Args:
        status (int): HTTP status code.
        data (str): Response data to include.

    Returns:
        JSONResponse: Formatted response object.
    """
    response_data = WebScraperResponse(status=status, data=data)
    return JSONResponse(content=response_data.model_dump(), status_code=status)


def calculate_md5(text: str) -> str:
    """
    Calculates the MD5 hash of a given text.

    Args:
        text (str): The input text to hash.

    Returns:
        str: MD5 hash of the input text.
    """
    if not text:
        raise ValueError("Input text is empty or None.")
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def clean_html_with_bs4(html_content: str) -> str:
    """
    Cleans HTML, keeping only allowed tags (h1-h6, p, a, span, etc.) and text.
    If a disallowed tag contains allowed tags, it is "unwrapped" (unwrap).
    Otherwise, it is entirely removed (decompose).
    Additionally, links (<a>) that are not embedded within text containers are removed.
    """
    if not html_content.strip():
        raise ValueError("HTML content must be a non-empty string.")
    soup = BeautifulSoup(html_content, "html.parser")
    allowed_tags = {
        "h1", "h2", "h3", "h4", "h5", "h6", "p", "a", "span", "strong", "b", "u",
        "s", "mark", "small", "blockquote", "q", "ul", "ol", "li", "abbr", "div",
        "table", "thead", "tbody", "tr", "th", "td",
    }
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    for comment in comments:
        comment.extract()
    def clean_tag(tag):
        for child in tag.contents[:]:
            if child.name:
                if child.name not in allowed_tags:
                    has_allowed_descendant = any(
                        (descendant.name in allowed_tags) 
                        for descendant in child.descendants
                    )
                    if has_allowed_descendant:
                        clean_tag(child)
                        child.unwrap()
                    else:
                        child.decompose()
                else:
                    clean_tag(child)
            else:
                if not child.strip():
                    child.extract()
    clean_tag(soup)
    for tag in soup.find_all():
        if tag.name in allowed_tags and not tag.get_text(strip=True):
            tag.decompose()
    text_containers = {
        "p", "h1", "h2", "h3", "h4", "h5", "h6", "span", "q", "blockquote", "li"
    }
    for a_tag in soup.find_all("a"):
        parent = a_tag.parent
        if parent and hasattr(parent, "name"):
            if parent.name not in text_containers:
                a_tag.decompose()
            else:
                parent_text = parent.get_text(strip=True)
                link_text = a_tag.get_text(strip=True)
                if parent_text == link_text:
                    a_tag.decompose()
    return str(soup)


def clean_page(page: str) -> str:
    """
    Cleans the given HTML page content.

    This function performs the following steps:
    1. Cleans the HTML content using BeautifulSoup.
    2. Converts the cleaned HTML to Markdown format.
    3. Cleans the text content of the page.

    Args:
        page (str): The HTML content of the page to be cleaned.

    Returns:
        str: The cleaned text content of the page.
    """
    if not page.strip():
        raise ValueError("Page content must be a non-empty string.")
    cleaned_page = clean_html_with_bs4(page)
    cleaned_page = md(cleaned_page)
    cleaned_page = clean_text(cleaned_page)
    return cleaned_page


async def delete_chunk_from_chromadb(
    chromadb_collection,
    url: str,
    chunk_number: int
) -> None:
    """
    Asynchronously deletes a specific chunk from a ChromaDB collection.

    Args:
        chromadb_collection: The ChromaDB collection from which the chunk will be deleted.
        url (str): The URL associated with the chunk to be deleted.
        chunk_number (int): The chunk number to be deleted.

    Returns:
        None
    """
    await chromadb_collection.delete(
        where={
            "$and": [
                {"url": {"$eq": url}},
                {"chunk_number": {"$eq": chunk_number}}
            ]
        }
    )


def get_last_version(collection: MongoCollection, url: str) -> int:
    """
    Retrieves the last (maximum) version `version` for a given `url`
    and returns the next value (`+1`) to ensure auto-increment.

    Args:
        collection (MongoCollection): The MongoDB collection where records are stored.
        url (str): The URL for which the version needs to be retrieved.

    Returns:
        int: The next version (`version + 1`). If no records exist for the given `url`,
             it starts from `1`.
    """
    last_record = collection.find_one(
        {"url": url},
        sort=[("version", pymongo.DESCENDING)],
        projection=["version"]
    )
    return (last_record["version"] + 1) if last_record else 1


async def save_to_mongo_and_update_vector_db(
    result: str,
    url: str,
    description: str,
    owner: str
) -> None:
    """
    Saves the extracted content to MongoDB and updates the vector database.

    Args:
        result (str): Extracted static text from the web page.
        url (str): The URL of the web page.
        description (str): Description of the web page.
        owner (str): The owner of the web page.
    Returns:
        None
    """
    current_date = datetime.datetime.now(datetime.timezone.utc)
    webscraper_colection_name = "webscraper"
    archive_collection_name = "archive"
    collection = mongo_db.get_or_create_collection(
        webscraper_colection_name,
        ("url", pymongo.ASCENDING),
        ("version", pymongo.DESCENDING)
    )
    collection_archive = mongo_db.get_or_create_collection(
        archive_collection_name,
        ("url", pymongo.ASCENDING),
        ("version", pymongo.DESCENDING)
    )
    chroma_client = await anext(get_chromadb_client())
    embedding_function = initialize_embedding_function()
    chromadb_collection = await chroma_client.get_or_create_collection(
        name=webscraper_colection_name,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"}
    )
    existing_record = collection.find_one(
        {"url": url},
        sort=[("version", pymongo.DESCENDING)]
    )
    checksum = calculate_md5(result)
    chunks = split_text_into_chunks(result)
    record_id = str(uuid.uuid4())
    new_record = {
        "_id": record_id,
        "url": url,
        "description": description,
        "response": result,
        "md5": checksum,
        "date": str(current_date),
        "version": get_last_version(collection, url),
        "owner": owner
    }
    if existing_record:
        existing_checksum = existing_record.get("md5", "")
        if existing_checksum == checksum:
            logger.info("No changes detected. Skipping update.")
            return
        logger.info("Content changed. Updating MongoDB and VectorDB.")
        existing_chunks = await chromadb_collection.get(
            where={"url": url}
        )
        existing_chunks = sorted(
            existing_chunks["metadatas"],
            key=lambda chunk: chunk["chunk_number"]
        )
        existing_chunks_length, new_chunks_length = len(existing_chunks), len(chunks)
        if existing_chunks_length > 0:
            description = (
                description if description != "Brief description of the webpage."
                else existing_chunks[0]["description"]
            )
            owner = (
                owner if owner != "FEI STU"
                else existing_chunks[0]["owner"]
            )
            new_record["owner"] = owner
            new_record["description"] = description
        for chunk_number in range(new_chunks_length):
            needs_update = True
            current_chunk = chunks[chunk_number]
            new_chunk_md5 = calculate_md5(current_chunk)
            if chunk_number < existing_chunks_length:
                existing_chunk_md5 = existing_chunks[chunk_number]["chunk_md5"]
                needs_update = existing_chunk_md5 != new_chunk_md5
            if not needs_update:
                continue
            await delete_chunk_from_chromadb(
                chromadb_collection,
                url,
                chunk_number
            )
            await chromadb_collection.upsert(
                ids=[f"{record_id}-{chunk_number}"],
                metadatas=[{
                    "url": url,
                    "description": description,
                    "md5": checksum,
                    "date": str(current_date),
                    "owner": owner,
                    "chunk_number": chunk_number,
                    "chunk_md5": new_chunk_md5
                }],
                documents=[current_chunk],
            )
        for chunk_number in range(new_chunks_length, existing_chunks_length):
            await delete_chunk_from_chromadb(
                chromadb_collection,
                url,
                chunk_number
            )
        collection.delete_one({"url": url})
        collection.insert_one(new_record)
        collection_archive.insert_one(new_record)
        logger.info("Record updated in both MongoDB and VectorDB.")
    else:
        logger.info("No existing record found. Inserting new record.")
        ids = [f"{record_id}-{chunk_number}" for chunk_number in range(len(chunks))]
        metadatas = [{
            "url": url,
            "description": description,
            "md5": checksum,
            "date": str(current_date),
            "owner": owner,
            "chunk_number": chunk_number,
            "chunk_md5": calculate_md5(chunks[chunk_number])
        } for chunk_number in range(len(chunks))]
        await chromadb_collection.upsert(
            ids=ids,
            metadatas=metadatas,
            documents=chunks,
        )
        collection.insert_one(new_record)
        collection_archive.insert_one(new_record)
        logger.info("New record inserted into MongoDB and VectorDB.")


async def extract_page_content(url: str, message: str, owner: str) -> JSONResponse:
    """
    Extracts static text content from the provided web page URL.

    Args:
        url (str): The URL of the web page to extract content from.
        message (str): Description of the web page.
        owner (str): The owner of the web page.

    Returns:
        JSONResponse: Response containing the extracted data or an error message.
    """
    logger.info("Starting extract_page_content function...")
    if not url:
        error_msg = "Invalid URL: URL is empty or None."
        return return_response_in_scrapper_format(
            status.HTTP_400_BAD_REQUEST,
            error_msg
        )
    if not message:
        error_msg = "Invalid message: message is empty or None."
        return return_response_in_scrapper_format(
            status.HTTP_400_BAD_REQUEST,
            error_msg
        )
    try:
        response = requests.get(url, timeout=15)
        if not response:
            error_msg = "Extracted data is empty"
            return return_response_in_scrapper_format(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_msg
            )
        if response.status_code != status.HTTP_200_OK:
            return return_response_in_scrapper_format(
                response.status_code,
                response.reason
            )
        result = clean_page(response.text)
        if not result.strip():
            error_msg = "Extracted content is empty after cleaning"
            return return_response_in_scrapper_format(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_msg
            )
        await save_to_mongo_and_update_vector_db(
            result=result,
            url=url,
            description=message,
            owner=owner
        )
        success_msg = "Operation has been completed successfully"
        return return_response_in_scrapper_format(
            status.HTTP_200_OK,
            success_msg
        )
    except ValueError as ve:
        error_msg = f"ValueError: {str(ve)}"
        return return_response_in_scrapper_format(
            status.HTTP_400_BAD_REQUEST,
            error_msg
        )
    except requests.exceptions.RequestException as re_e:
        error_msg = f"RequestException: {str(re_e)}"
        return return_response_in_scrapper_format(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            error_msg
        )
    except ConnectionError as ce:
        error_msg = f"ConnectionError: {str(ce)}"
        return return_response_in_scrapper_format(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            error_msg
        )
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        return return_response_in_scrapper_format(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_msg
        )
