import os
import streamlit as st
from httpx import BasicAuth, AsyncClient, Timeout, HTTPError, ReadTimeout, Response, ConnectTimeout
from common.session.decorators import http_timer
from common.logging.st_logger import st_logger


BASE_URL = "http://backend:8080"

# Load nginx credentials from .env
# Please define GUI_PASSWORD in your local .env
USERNAME = "admin"
PASSWORD = os.getenv("GUI_PASSWORD")


# Function that converts st.file_uploader UploadedFile instance to fastAPI UploadFile instance
def convert_file_to_UploadFile(file_data, file_name, file_type):
    file = {"file": (file_name, file_data, file_type)}
    return file


# Returns TRUE if igestion was successful
def is_api_call_successful(response):
    # Simple solution until better option presents itself
    return response.status_code == 201 or response.status_code == 200


"""

All functions bellow return a httpx.Response class instance.

"""

# Asynchronous function to check backend server status


@http_timer
async def get_status():
    # Basic authentication credentials
    auth = BasicAuth(USERNAME, PASSWORD)

    async with AsyncClient(auth=auth) as client:
        response = await client.get(BASE_URL + "/api/status")

    return response


# Asynchronous function that handles file ingest
@http_timer
async def post_ingest_file(file):

    try:
        async with AsyncClient(timeout=Timeout(300.0, connect=10.0)) as client:
            response = await client.post(BASE_URL+"/api/ingest_file", files=file)
        return response
    except ReadTimeout:
        st_logger.error("Read timeout occurred when ingesting file: " + file.name)
        st.toast(st.session_state.translator("⚠️Read timeout occurred. Failed to learn: ") + file.name)
        return Response(status_code=504)
    except ConnectTimeout:
        st_logger.error("Connection timeout occurred when ingesting file: " + file.name)
        st.toast(st.session_state.translator("⚠️Connection timeout occurred. Failed to learn: ") + file.name)
        return Response(status_code=504)
    except HTTPError as e:
        st_logger.error(f"HTTP error occurred when ingesting file: {file.name}: {e}")
        st.toast(st.session_state.translator("⚠️HTTP error occurred. Failed to learn: ") + file.name)
        return Response(status_code=500)
    except Exception as e:
        st_logger.error(f"An error occurred when ingesting file: {file.name}: {e}")
        st.toast(st.session_state.translator("⚠️Something went wrong. Failed to learn: ") + file.name)
        return Response(status_code=500)


# Asynchronous function that handles text ingest
@http_timer
async def post_ingest_text(text, content_type="text/plain"):

    headers = {"Content-Type": content_type}

    async with AsyncClient() as client:
        if content_type == "application/json":
            # If the content type is JSON, send the text in JSON format
            response = await client.post(
                f"{BASE_URL}/api/ingest_text",
                headers=headers,
                json={"text": text}
            )
        else:
            # For other content types like plain text
            response = await client.post(
                f"{BASE_URL}/api/ingest_text",
                headers=headers,
                content=text
            )

    return response


# Asynchronous function that retrieve data from ChromaDB
@http_timer
async def get_retrieve_data(text, filename=None, user=None, date=None, n_results=None):

    # Prepare query parameters
    params = {
        "text": text,
        "filename": filename,
        "user": user,
        "date": date,
        "n_results": n_results
    }

    # Filter out parameters with None values
    params = {k: v for k, v in params.items() if v is not None}

    async with AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/retrieve_data", params=params)

    return response


# Asynchronous function that deletes ingested data from ChromaDB
@http_timer
async def delete_delete_data(file_name, user=None, date=None):

    # Prepare query parameters
    params = {
        "file_name": file_name,
        "user": user,
        "date": date,
    }

    # Filter out parameters with None values
    params = {k: v for k, v in params.items() if v is not None}
    async with AsyncClient() as client:
        response = await client.delete(f"{BASE_URL}/api/delete_data", params=params)

    return response


@http_timer
async def post_webscraper(url: str, description: str, owner: str) -> dict:
    """
    Async function that sends a POST request to the webscraper endpoint.

    Args:
        url (str): URL of the website to scrape from
        description (str): Description of the website
        owner (str): Owner of the website

    Returns:
        dict: Response from the endpoint

    """

    body = {
        "url": url,
        "description": description,
        "owner": owner
    }
    async with AsyncClient(timeout=Timeout(60.0, connect=10.0)) as client:
        response = await client.post(f"{BASE_URL}/api/webscraper/webscraper", json=body)
    return response


@http_timer
async def delete_delete_one_mongo_record(collection_name: str, _id: str) -> dict:
    """
    Function that deletes one record from the MongoDB

    Args:
        collection_name (str): Name of the collection to delete from
        filter (dict):Filter of the record to delete

    Returns:
        dict: Response from the endpoint

    """

    body = {
        "collection_name": collection_name,
        "filter": {"_id": _id}
    }
    async with AsyncClient() as client:
        response = await client.request('DELETE', f"{BASE_URL}/api/common/delete_one_mongo_record", json=body)
    return response


@http_timer
async def delete_delete_one_chroma_record(collection_name: str, filter: dict) -> dict:
    """
    Function that deletes one record from the MongoDB

    Args:
        collection_name (str): Name of the collection to delete from
        filter (dict): Filter to find the record to delete

    Returns:
        dict: Response from the endpoint

    """

    body = {
        "collection_name": collection_name,
        "filter": filter
    }
    async with AsyncClient() as client:
        response = await client.request('DELETE', f"{BASE_URL}/api/common/delete_one_chroma_record", json=body)
    return response


@http_timer
async def post_faq_load_records(question: str, answer: str, doc: str = None, url: str = None) -> dict:
    """
    Async function that sends a POST request to create new FAQ record.

    Args:
        question (str): Question to be added to the FAQ
        answer (str): Answer to the question
        doc (str): Document where the answer can be found
        url (str): URL where the answer can be found

    Returns:
        dict: Response from the endpoint

    """

    body = [{
        "question": question,
        "answer": answer,
    }]
    async with AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/faq/load_records", json=body)
    return response


@http_timer
async def post_faq_random_questions(collection: str, random: int) -> dict:
    """
    Async function that sends a POST request to get random FAQ questions.

    Args:
        collection (str): Name of the collection to get questions from
        random (int): Number of random questions to retrieve

    Returns:
        dict: Response from the endpoint

    """

    body = [{
        "collection": collection,
        "random": random
    }]
    async with AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/faq/random_questions", json=body)
    return response


@http_timer
async def post_get_rag_answer(content: str) -> dict:
    """
    Async function that sends a POST request to get LLM answer.

    Args:
        content (str): Content to get answer for

    Returns:
        dict: Response from the endpoint

    """
    URL = "http://llm:8507"

    body = [{
        "role": "user",
        "content": content
    }]
    async with AsyncClient(timeout=Timeout(60.0, connect=10.0)) as client:
        response = await client.post(f"{URL}/llm/get_rag_answer", json=body)
    return response
