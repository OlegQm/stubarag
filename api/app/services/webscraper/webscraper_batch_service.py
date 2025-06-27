from typing import List, Dict, Any
import datetime
import uuid
import json
import asyncio
import logging
import time

import requests
import pymongo
import tiktoken
import openai
from fastapi import status
from fastapi.responses import JSONResponse
from pymongo.collection import Collection as MongoCollection
from chromadb.api.models import Collection as ChromaCollection

from app.routers.schemas import Page
from app.database import mongo_db, get_chromadb_client
from app.utils import EMBEDDING_MODEL, OPENAI_API_KEY
from app.routers.schemas import WebScraperBatchResponse
from app.services.webscraper.webscraper_service import (
    calculate_md5,
    split_text_into_chunks,
    delete_chunk_from_chromadb,
    clean_page,
    get_last_version
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)

openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
MAX_TIME_IN_SECONDS = 30 * 3600


def return_response_in_webscraper_batch_format(
    status: int,
    message: str,
    pages_statuses: List[Dict[str, List[Any]]]
) -> JSONResponse:
    """
    Constructs and returns a JSONResponse in the standardized webscraper batch format.

    status (int): The HTTP status code to return.
    message (str): A descriptive message about the response.
    pages_statuses (List[Dict[str, List[Any]]]): A list containing the status information for each processed page.

    JSONResponse: A response object containing the formatted batch response data and the specified HTTP status code.
    """
    logger.info(
        f"Returning response with status {status}: {message}",
        extra={"pages_statuses": pages_statuses}
    )
    response_data = WebScraperBatchResponse(
        status=status,
        message=message,
        is_webpage_updated=pages_statuses
    )
    return JSONResponse(content=response_data.model_dump(), status_code=status)


def get_unique_pages(pages: List[Page]) -> List[Page]:
    """
    Filters the given list of pages to ensure uniqueness based on the URL.

    Args:
        pages (List[Page]): A list of Page objects containing URL, description, and owner.

    Returns:
        List[Page]: A list of unique Page objects with no duplicate URLs.
    """
    logger.info(f"Filtering {len(pages)} pages for uniqueness.")
    if not isinstance(pages, list):
        logger.error("Expected a list of Page objects")
        raise TypeError("Expected a list of Page objects")
    seen_urls = set()
    unique_objects = []
    for page in pages:
        if not page.url.strip():
            logger.error("Page URL must be a non-empty string")
            raise ValueError("Page URL must be a non-empty string")
        if page.url not in seen_urls:
            unique_objects.append(page)
            seen_urls.add(page.url)
    logger.info(f"Found {len(unique_objects)} unique pages.")
    return unique_objects


def request_and_clean_pages(pages: List[Page]) -> List[Dict[str, Any]]:
    """
    Fetches and processes the content of a list of web pages.

    This function sends HTTP GET requests to each page in the provided list, cleans the retrieved HTML content,
    and collects the results. It also tracks the status of each request, including any errors encountered.

        pages (List[Page]): A list of Page objects, each containing a URL, description, and owner.

        Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
            - A list of dictionaries with cleaned page data, including 'url', 'description', 'owner', and 'text'.
            - A list of dictionaries mapping each URL to its HTTP status code and a descriptive message.
    """
    unique_pages_list = []
    pages_statuses = []
    logger.info(f"Requesting and cleaning {len(pages)} pages.")
    for page in pages:
        try:
            logger.info(f"Requesting URL: {page.url}")
            response = requests.get(page.url, timeout=15)
            if not response:
                error_msg = "Extracted data is empty"
                logger.error(f"Failed to get response for {page.url}: {error_msg}")
                raise requests.exceptions.RequestException(
                    error_msg
                )
            response.raise_for_status()
            if response.status_code != 200:
                logger.error(f"Non-200 status for {page.url}: {response.status_code}")
                raise requests.exceptions.RequestException(
                    response.reason
                )
            text_cleaned = clean_page(response.text)
            if not text_cleaned.strip():
                logger.error(f"The page content is empty for {page.url}")
                raise ValueError("The page content is empty")
            unique_pages_list.append(
                {
                    "url": page.url,
                    "description": page.description,
                    "owner": page.owner,
                    "text": text_cleaned
                }
            )
            pages_statuses.append(
                {
                    page.url: [
                        status.HTTP_200_OK,
                        "Page content successfully extracted"
                    ]
                }
            )
            logger.info(f"Successfully processed {page.url}")
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout while requesting {page.url}")
            pages_statuses.append(
                {
                    page.url: [
                        status.HTTP_408_REQUEST_TIMEOUT,
                        "Request timed out"
                    ]
                }
            )
            continue
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error while requesting {page.url}")
            pages_statuses.append(
                {
                    page.url: [
                        status.HTTP_503_SERVICE_UNAVAILABLE,
                        "Connection error"
                    ]
                }
            )
            continue
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request failed for {page.url}: {str(e)}")
            pages_statuses.append(
                {
                    page.url: [
                        status.HTTP_404_NOT_FOUND,
                        f"HTTP request failed for {page.url}: {str(e)}"
                    ]
                }
            )
            continue
        except Exception as e:
            logger.error(f"An unexpected error occurred for {page.url}: {str(e)}")
            pages_statuses.append(
                {
                    page.url: [
                        status.HTTP_500_INTERNAL_SERVER_ERROR,
                        f"An unexpected error occurred: {str(e)}"
                    ]
                }
            )
            continue

    logger.info(f"Finished requesting and cleaning pages. {len(unique_pages_list)} succeeded, {len(pages_statuses)} statuses collected.")
    return unique_pages_list, pages_statuses


def check_page_needs_update(
    mongodb_collection: MongoCollection,
    pages: List[Dict[str, Any]]
) -> List[bool]:
    """
    Checks whether each page in the list needs to be updated in the MongoDB and ChromaDB.

    Args:
        mongodb_collection (MongoCollection): The MongoDB collection containing page data.
        pages (List[Dict[str, Any]]): A list of dictionaries containing page data.

    Returns:
        List[bool]: A list indicating if each page needs an update or insertion.
    """
    logger.info(f"Checking if {len(pages)} pages need update.")
    pages_needs_update = []
    for page in pages:
        url = page.get("url", "")
        existing_record = mongodb_collection.find_one(
            {"url": url},
            sort=[("version", pymongo.DESCENDING)]
        )
        new_md5 = calculate_md5(page.get("text", ""))

        if existing_record:
            existing_md5 = (
                existing_record.get("md5", "") if existing_record
                else ""
            )
            needs_update_or_insert = [
                existing_md5 != new_md5,
                existing_md5 != new_md5,
                new_md5
            ]
            logger.info(f"Page {url}: existing_md5={existing_md5}, new_md5={new_md5}, needs_update={existing_md5 != new_md5}")
            pages_needs_update.append(needs_update_or_insert)
            continue
        logger.info(f"Page {url} is new and needs to be inserted.")
        pages_needs_update.append([True, False, new_md5])
    return pages_needs_update


def count_tokens(text: str) -> int:
    """
    Counts the number of tokens in the text using the cl100k_base encoding.

    Args:
        text (str): The text to be tokenized.

    Returns:
        int: The number of tokens in the text.
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


async def get_changed_chunks(
    chromadb_collection: ChromaCollection,
    page: Dict[str, Any],
    chunks: List[str]
) -> List[Dict[str, Any]]:
    """
    Identifies changed chunks for a page and calculates metadata for each chunk.

    Args:
        chromadb_collection (ChromaCollection): The ChromaDB collection to compare against.
        page (Dict[str, Any]): A dictionary containing page data.
        chunks (List[str]): A list of chunks for the given page.

    Returns:
        List[Dict[str, Any]]: A dictionary containing the changed chunks and associated metadata.
    """
    url = page.get("url", "")
    logger.info(f"Getting changed chunks for {url}")
    existing_chunks_length, new_chunks_length = -1, len(chunks)
    changed_chunks = []
    existing_chunks = []
    is_not_new_record = page.get("is_not_new_record", True)

    if is_not_new_record:
        response = await chromadb_collection.get(
            where={"url": url},
            include=["metadatas"]
        )
        if (
            not response
            or "metadatas" not in response
            or not response["metadatas"]
        ):
            response = {"metadatas": []}

        existing_chunks = sorted(
            response["metadatas"],
            key=lambda chunk: chunk.get("chunk_number", float('inf'))
        )
        existing_chunks_length = len(existing_chunks)
        if existing_chunks_length > 0:
            page_description = page["description"]
            page_owner = page["owner"]
            page["description"] = (
                page_description
                if page_description != "Brief description of the webpage."
                else existing_chunks[0]["description"]
            )
            page["owner"] = (
                page_owner if page_owner != "FEI STU"
                else existing_chunks[0]["owner"]
            )

    for chunk_number in range(new_chunks_length):
        needs_update = True
        delete_old_record_in_chroma = False
        current_chunk = chunks[chunk_number]
        new_chunk_md5 = calculate_md5(current_chunk)
        if chunk_number < existing_chunks_length:
            existing_chunk_md5 = existing_chunks[chunk_number]["chunk_md5"]
            needs_update = existing_chunk_md5 != new_chunk_md5
            delete_old_record_in_chroma = existing_chunk_md5 != new_chunk_md5
        if not needs_update:
            continue
        changed_chunks.append(
            {
                "chunk_number": chunk_number,
                "chunk_text": current_chunk,
                "chunk_md5": new_chunk_md5,
                "tokens_in_chunk": count_tokens(current_chunk),
                "delete_old_record_in_chroma": delete_old_record_in_chroma
            }
        )
        logger.info(f"Chunk {chunk_number} for {url} marked as changed (needs_update={needs_update}).")
    logger.info(f"Total changed chunks for {url}: {len(changed_chunks)}")
    return {
        "url": url,
        "description": page.get("description", ""),
        "md5": page.get("md5", ""),
        "owner": page.get("owner", ""),
        "changed_chunks": changed_chunks,
        "existing_chunks_length": existing_chunks_length,
        "new_chunks_length": new_chunks_length
    }


async def split_texts_and_format_chunks(
    chromadb_collection: ChromaCollection,
    pages: List[Dict[str, Any]],
    pages_statuses: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Asynchronously splits the text content of each page into chunks, compares them with an existing ChromaDB collection,
    and formats the results by identifying changed chunks.

        chromadb_collection (ChromaCollection): The ChromaDB collection used to detect changes in text chunks.
        pages (List[Dict[str, Any]]): A list of dictionaries, each containing data for a single page, including its text.
        pages_statuses (List[Dict[str, Any]]): A list to which error statuses and messages will be appended for pages
            that encounter issues during processing.

        List[Dict[str, Any]]: A list of dictionaries, each containing the changed chunks and associated metadata for a page.

    Workflow:
        - Iterates through each page, splitting its text into chunks.
        - Handles and logs errors during chunking, updating pages_statuses as needed.
        - For successfully chunked pages, compares chunks with the ChromaDB collection to identify changes.
        - Collects and returns the results for all pages with detected changes.
    """
    logger.info(f"Splitting and formatting chunks for {len(pages)} pages.")
    chunked_pages = []
    for page in pages:
        text = page.get("text", "")
        try:
            chunks = split_text_into_chunks(text)
        except ValueError as e:
            logger.error(
                f"Error splitting text into chunks for page {page.get('url', 'unknown')}: {e}"
            )
            pages_statuses.append(
                {
                    page.get("url", "unknown"): [
                        status.HTTP_500_INTERNAL_SERVER_ERROR,
                        f"Error splitting text into chunks: {str(e)}"
                    ]
                }
            )
            continue
        if not chunks:
            logger.warning(f"No chunks produced for {page.get('url', 'unknown')}")
            continue
        logger.info(f"Page {page.get('url', 'unknown')} split into {len(chunks)} chunks.")
        chunked_pages.append(
            await get_changed_chunks(
                chromadb_collection,
                page,
                chunks
            )
        )
    logger.info(f"Total pages with changed chunks: {len(chunked_pages)}")
    return chunked_pages


def process_single(
    chunks_to_send_identifiers: List[Dict[str, int]],
    chunks_to_send: List[str],
    changed_chunks: List[Dict[str, Any]]
) -> None:
    """
    Process each chunk via single embeddings calls to OpenAI (instead of batch).
    
    Args:
        chunks_to_send_identifiers (List[Dict[str, int]]): Identifiers for chunks (page index, chunk ID, etc.).
        chunks_to_send (List[str]): List of chunk texts that need embeddings.
        changed_chunks (List[Dict[str, Any]]): The list of pages and their modified chunks where embeddings are stored.

    Returns:
        None: The function updates the 'changed_chunks' structure in place with retrieved embeddings.
    """
    logger.info(f"Processing {len(chunks_to_send)} chunks via single OpenAI calls.")
    for identifier, chunk_text in zip(
        chunks_to_send_identifiers,
        chunks_to_send
    ):
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=[chunk_text]
        )
        embedding = response.data[0].embedding
        page_index = identifier["page_index"]
        changed_chunks[page_index].setdefault("chunks_embeddings", []).append(embedding)
    logger.info("Embeddings successfully obtained via single calls.")
    return


async def process_chunks(
    chunks_to_send: List[str],
    chunks_to_send_identifiers: List[Dict[str, int]],
    changed_chunks: List[Dict[str, Any]],
    start_time: float,
    batch_metadata: Dict[str, Any] = None
) -> None:
    """
    Sends chunks for processing to OpenAI using Batch API and stores embeddings in the corresponding pages.

    Args:
        chunks_to_send (List[str]): List of chunk texts to be processed.
        chunks_to_send_identifiers (List[Dict[str, int]]): List of chunk identifiers.
        changed_chunks (List[Dict[str, Any]]): Original list of pages with modified chunks.
        batch_metadata (Dict[str, Any]): Additional metadata for the batch (optional).
    """
    if not chunks_to_send:
        logger.info("No chunks to send for embedding.")
        return

    if time.time() - start_time > MAX_TIME_IN_SECONDS:
        logger.warning("Max time exceeded, falling back to single embedding calls.")
        process_single(
            chunks_to_send_identifiers=chunks_to_send_identifiers,
            chunks_to_send=chunks_to_send,
            changed_chunks=changed_chunks
        )
        return

    fallback_to_single = False

    jsonl_data = [
        {
            "custom_id": str(chunks_to_send_identifiers[i]["chunk_id"]),
            "method": "POST",
            "url": "/v1/embeddings",
            "body": {
                "input": chunk,
                "model": EMBEDDING_MODEL
            }
        }
        for i, chunk in enumerate(chunks_to_send)
    ]

    file_content = "\n".join(json.dumps(entry) for entry in jsonl_data).encode("utf-8")

    logger.info(f"Uploading file with {len(jsonl_data)} entries for batch embedding.")
    uploaded_file = openai_client.files.create(
        file=file_content,
        purpose="batch"
    )
    file_id = uploaded_file.id

    batch = openai_client.batches.create(
        input_file_id=file_id,
        endpoint="/v1/embeddings",
        completion_window="24h",
        metadata=batch_metadata or {"description": "Embedding processing batch"}
    )
    batch_id = batch.id
    logger.info(f"Batch created with ID: {batch_id}")

    while True:
        if time.time() - start_time > MAX_TIME_IN_SECONDS:
            logger.warning(
                "Batch processing took more than 30 hours. Fallback to single calls."
            )
            fallback_to_single = True
            break

        current_status = openai_client.batches.retrieve(batch_id)
        logger.info(f"Batch {batch_id} status: {current_status.status}")
        if current_status.status not in [
            "in_progress",
            "finalizing",
            "cancelling",
            "validating"
        ]:
            break
        await asyncio.sleep(5)

    if fallback_to_single:
        logger.warning(f"Cancelling batch {batch_id} and switching to single embedding calls.")
        openai_client.batches.cancel(batch_id)
        process_single(
            chunks_to_send_identifiers=chunks_to_send_identifiers,
            chunks_to_send=chunks_to_send,
            changed_chunks=changed_chunks
        )
        return

    if current_status.status == "completed":
        output_file_id = current_status.output_file_id
        logger.info(f"Batch {batch_id} completed. Downloading results from file {output_file_id}.")
        result_file = openai_client.files.content(output_file_id)
        results = [
            json.loads(line)
            for line in result_file.text.splitlines()
        ]

        chunk_id_to_page_index = {
            str(identifier['chunk_id']): identifier['page_index']
            for identifier in chunks_to_send_identifiers
        }

        for result in results:
            custom_id = result["custom_id"]
            response = result["response"]

            if (
                not response
                or "body" not in response
                or not response["body"].get("data")
            ):
                logger.error(f"Failed to retrieve embedding for custom_id: {custom_id}")
                raise openai.OpenAIError(
                    f"Failed to retrieve embedding for custom_id: {custom_id}"
                )

            embedding_data = response["body"]["data"][0]
            if "embedding" in embedding_data:
                embedding = embedding_data["embedding"]
                page_index = chunk_id_to_page_index.get(custom_id, None)
                if page_index is None:
                    logger.error(f"Page index is None for custom_id: {custom_id}")
                    raise ValueError("Page index is None")
                if page_index < len(changed_chunks):
                    embedding_page = changed_chunks[page_index]
                    embedding_page.setdefault("chunks_embeddings", []).append(embedding)

        logger.info("Embeddings successfully updated from batch.")
    else:
        logger.error(f"Batch failed with status: {current_status.status}")
        raise openai.OpenAIError(
            f"Batch failed with status: {current_status.status}"
        )


async def get_openai_embeddings(
    changed_chunks: List[Dict[str, Any]]
) -> Dict[str, List[Any]]:
    """
    Processes changed chunks to retrieve embeddings from OpenAI and updates the changed chunks with embeddings.

    Args:
        changed_chunks (List[Dict[str, Any]]): A list of dictionaries containing page data
                                               and their respective changed chunks.

    Returns:
        Dict[str, List[Any]]: The updated list of changed chunks with embeddings and date appended.
    """
    tokens_limit = 2500
    total_tokens = 0
    chunks_to_send_identifiers = []
    chunks_to_send = []
    chunk_id = 0

    global_start_time = time.time()
    logger.info(f"Processing OpenAI embeddings for {len(changed_chunks)} pages.")
    for page_index, page in enumerate(changed_chunks):
        current_date = str(datetime.datetime.now(datetime.timezone.utc))
        page["chunks_embeddings"] = []
        page["date"] = current_date

        for chunk in page.get("changed_chunks", []):
            if total_tokens + chunk.get("tokens_in_chunk", 0) <= tokens_limit:
                chunk_text = chunk.get("chunk_text")
                if not chunk_text:
                    logger.warning(f"Chunk text is empty for page index {page_index}")
                    continue
                total_tokens += chunk.get("tokens_in_chunk", 0)
                chunks_to_send_identifiers.append(
                    {
                        "page_index": page_index,
                        "chunk_id": chunk_id
                    }
                )
                chunks_to_send.append(chunk_text)
                chunk_id += 1
            else:
                logger.info(f"Token limit reached, sending {len(chunks_to_send)} chunks for embedding.")
                await process_chunks(
                    chunks_to_send,
                    chunks_to_send_identifiers,
                    changed_chunks,
                    global_start_time
                )
                total_tokens = 0
                chunks_to_send_identifiers = []
                chunks_to_send = []

                total_tokens += chunk.get("tokens_in_chunk", 0)
                chunks_to_send_identifiers.append(
                    {
                        "page_index": page_index,
                        "chunk_id": chunk_id
                    }
                )
                chunks_to_send.append(chunk_text)
                chunk_id += 1

    logger.info(f"Sending final {len(chunks_to_send)} chunks for embedding.")
    await process_chunks(
        chunks_to_send,
        chunks_to_send_identifiers,
        changed_chunks,
        global_start_time
    )

    logger.info("All embeddings processed.")
    return changed_chunks


async def extract_pages_content(pages: List[Page]) -> JSONResponse:
    """
    Asynchronously scrapes web pages and processes their content.

    Args:
        pages (List[Page]): A list of Page objects containing the URL, description,
        and owner information for each page to be scraped.

    Returns:
        WebScraperResponse: The response object containing the results of the web scraping operation.
    """
    logger.info("Starting extraction of pages content.")
    unique_pages = get_unique_pages(pages)
    try:
        unique_pages, pages_statuses = request_and_clean_pages(unique_pages)
        if not unique_pages:
            logger.error("No valid pages found after cleaning.")
            raise requests.exceptions.RequestException(
                "No valid pages found after cleaning."
            )
        webscraper_collection_name = "webscraper"
        archive_collection_name = "archive"

        logger.info("Getting MongoDB collections.")
        collection = mongo_db.get_or_create_collection(
            webscraper_collection_name,
            ("url", pymongo.ASCENDING),
            ("version", pymongo.DESCENDING),
        )

        collection_archive = mongo_db.get_or_create_collection(
            archive_collection_name,
            ("url", pymongo.ASCENDING),
            ("version", pymongo.DESCENDING),
        )

        logger.info("Getting ChromaDB client and collection.")
        chroma_client = await anext(get_chromadb_client())
        chromadb_collection = await chroma_client.get_or_create_collection(
            name=webscraper_collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        logger.info("Checking which pages need update.")
        unique_pages_needs_update = check_page_needs_update(
            collection,
            unique_pages
        )

        unique_pages = [
            {
                **page,
                "is_not_new_record": flag[1],
                "md5": flag[2]
            } for page, flag in zip(
                unique_pages,
                unique_pages_needs_update
            ) if flag[0]
        ]

        logger.info(f"{len(unique_pages)} pages need to be updated.")
        changed_chunks = await split_texts_and_format_chunks(
            chromadb_collection,
            unique_pages,
            pages_statuses
        )
        logger.info("Getting OpenAI embeddings for changed chunks.")
        changed_chunks = await get_openai_embeddings(changed_chunks)
        for page_number, page in enumerate(changed_chunks):
            record_id = str(uuid.uuid4())
            embeddings = page.get("chunks_embeddings")
            for i, chunk in enumerate(page.get("changed_chunks")):
                ids = [f"{record_id}-{i}"]
                metadatas = [{
                    "url": page.get("url"),
                    "description": page.get("description"),
                    "md5": page.get("md5"),
                    "date": page.get("date"),
                    "owner": page.get("owner"),
                    "chunk_number": chunk.get("chunk_number"),
                    "chunk_md5": chunk.get("chunk_md5")
                }]
                if chunk.get("delete_old_record_in_chroma"):
                    logger.info(f"Deleting old chunk {chunk.get('chunk_number')} for {page.get('url')}")
                    await delete_chunk_from_chromadb(
                        chromadb_collection,
                        page.get("url"),
                        chunk.get("chunk_number")
                    )
                await chromadb_collection.upsert(
                    ids=ids,
                    metadatas=metadatas,
                    embeddings=[embeddings[i]],
                    documents=[chunk.get("chunk_text")]
                )
            page_url = page.get("url")
            new_mongo_record = {
                "_id": record_id,
                "url": page_url,
                "description": page.get("description"),
                "response": unique_pages[page_number].get("text"),
                "md5": page.get("md5"),
                "date": page.get("date"),
                "version": get_last_version(collection, page_url),
                "owner": page.get("owner")
            }
            for chunk in range(
                page.get("new_chunks_length"),
                page.get("existing_chunks_length")
            ):
                logger.info(f"Deleting extra chunk {chunk} for {page_url}")
                await delete_chunk_from_chromadb(
                    chromadb_collection,
                    page_url,
                    chunk
                )
            logger.info(f"Updating MongoDB for {page_url}")
            collection.delete_one({"url": page_url})
            collection.insert_one(new_mongo_record)
            collection_archive.insert_one(new_mongo_record)
        unique_urls = [uniqe_page['url'] for uniqe_page in unique_pages]
        unique_urls_len = len(unique_urls)
        logger.info(
            f"{unique_urls_len} pages successfully updated." +
            (" Their urls:\n" if unique_urls_len > 0 else "") +
            "\n".join(unique_urls)
        )
        status_codes = [list(status_info.values())[0][0] for status_info in pages_statuses]
        total = len(status_codes)
        success_count = status_codes.count(status.HTTP_200_OK)

        if total == 0:
            overall_status = status.HTTP_500_INTERNAL_SERVER_ERROR
            message = "No pages were processed successfully."
        elif success_count == total:
            overall_status = status.HTTP_200_OK
            message = "Operation has been completed successfully."
        elif success_count == 0:
            overall_status = status.HTTP_500_INTERNAL_SERVER_ERROR
            message = "All pages failed to process."
        else:
            overall_status = status.HTTP_207_MULTI_STATUS
            message = "Partial success: some pages failed to process."

        logger.info(f"Returning batch response: {message}")
        return return_response_in_webscraper_batch_format(
            overall_status,
            message,
            pages_statuses
        )
    except requests.exceptions.RequestException as re_e:
        error_msg = f"RequestException: {str(re_e)}"
        logger.error(error_msg)
        return return_response_in_webscraper_batch_format(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            error_msg,
            pages_statuses
        )
    except ValueError as ve:
        error_msg = f"ValueError: {str(ve)}"
        logger.error(error_msg)
        return return_response_in_webscraper_batch_format(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_msg,
            pages_statuses
        )
    except openai.OpenAIError as oe:
        error_msg = f"OpenAI Error: {str(oe)}"
        logger.error(error_msg)
        return return_response_in_webscraper_batch_format(
            status.HTTP_400_BAD_REQUEST,
            error_msg,
            pages_statuses
        )
    except Exception as e:
        error_msg = f"An error occurred while processing the pages: {str(e)}"
        logger.error(error_msg)
        return return_response_in_webscraper_batch_format(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_msg,
            pages_statuses
        )
