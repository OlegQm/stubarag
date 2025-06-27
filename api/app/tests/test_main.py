from datetime import date

from app.config import settings
from app.main import app
from fastapi import status
from fastapi.testclient import TestClient


"""

This module contains test cases for the API endpoints of the application.
It uses the FastAPI TestClient to simulate requests and validate responses.
The tests cover various endpoints including status check, file ingestion, text ingestion,
data retrieval, and data deletion.

"""

client = TestClient(app)

settings.chroma_collection_name = "test"
settings.dev_user = "devuser"

# Test cases:

# /ingest_file

def test_ingest_file_pdf():
    with open("app/tests/data/test.pdf", "rb") as f:
        response = client.post("/api/ingest_file", files={"file": f})
        assert response.status_code == 201
        assert response.json() == {
            "message": "PDF processed successfully",
            "metadatas": {
                "filename": "test.pdf",
                "date": str(date.today()),
                "user": settings.dev_user,
            },
        }


def test_ingest_file_missing_file():
    response = client.post("/api/ingest_file")
    assert response.status_code == 422

    response_json = response.json()
    assert "detail" in response_json

    details = response_json["detail"]
    assert len(details) > 0
    assert "loc" in details[0]
    assert details[0]["loc"] == ["body", "file"]


def test_ingest_file_unsupported_file():
    with open("app/tests/data/test.txt", "rb") as f:
        response = client.post("/api/ingest_file", files={"file": f})
        assert response.status_code == 415
        assert response.json() == {"detail": "Invalid content type"}


# /ingest_text


# Test case for ingesting plain text content.
# This test sends a POST request to the '/api/ingest_text' endpoint with a plain text document.
# It asserts that the response status code is 201 (indicating success) and that the response JSON
# contains the expected message.
def test_ingest_text_plain():
    text_content = "This is a test document"
    response = client.post(
        "/api/ingest_text", data=text_content, headers={"Content-Type": "text/plain"}
    )
    assert response.status_code == 201
    assert response.json() == {
        "message": "Text processed successfully",
        "metadatas": {
            "filename": "text",
            "date": str(date.today()),
            "user": settings.dev_user,
        },
    }


# Test case for ingesting plain text without the 'text' parameter.
# It sends a POST request to '/api/ingest_text' with 'Content-Type' header set to 'text/plain'.
# The expected behavior is a 400 status code and a JSON response with the detail message 'Text field is required'.
def test_ingest_text_plain_without_param():
    response = client.post(
        "/api/ingest_text", headers={"Content-Type": "text/plain"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Text field is required"}


# Test case for ingesting plain text with an empty string.
# This test sends a POST request to the '/api/ingest_text' endpoint with an empty string as the text content.
# It asserts that the response status code is 400 (indicating a bad request) and that the response JSON
# contains the expected error message.
def test_ingest_text_plain_empty_string():
    text_content = ""
    response = client.post(
        "/api/ingest_text", data=text_content, headers={"Content-Type": "text/plain"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Text field is required"}


def test_ingest_text_json():
    json_content = {"text": "This is a test document"}
    response = client.post(
        "/api/ingest_text",
        json=json_content,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {
        "message": "Text processed successfully",
        "metadatas": {
            "filename": "text",
            "date": str(date.today()),
            "user": settings.dev_user,
        },
    }


def test_ingest_text_json_empty_string():
    json_content = {"text": ""}
    response = client.post(
        "/api/ingest_text",
        json=json_content,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Text field is required"}


def test_ingest_text_json_no_data():
    response = client.post(
        "/api/ingest_text", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Invalid JSON format"}


def test_ingest_text_no_content_type():
    response = client.post("/api/ingest_text")
    assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    assert response.json() == {"detail": "Invalid content type"}


# /retrieve_data


def test_retrieve_data_with_text():
    text_content = "This is a test document"
    client.post(
        "/api/ingest_text", data=text_content, headers={"Content-Type": "text/plain"}
    )

    query_text = "test"
    response = client.get("/api/retrieve_data", params={"text": query_text})
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert "documents" in response.json()
    assert "content" in response_json["documents"][0]
    assert "metadata" in response_json["documents"][0]
    assert "This is a test document" in response_json["documents"][0]['content']


def test_retrieve_data_with_optional_params():
    text_content = "This is a test document"
    client.post(
        "/api/ingest_text", data=text_content, headers={"Content-Type": "text/plain"}
    )

    current_date = date.today().strftime("%Y-%m-%d")
    query_text = "test"
    response = client.get(
        "/api/retrieve_data",
        params={
            "text": query_text,
            "filename": "text",
            "user": settings.dev_user,
            "date": current_date,
            "n_results": 5,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert "documents" in response.json()


def test_retrieve_data_with_no_text():
    response = client.get("/api/retrieve_data")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "detail" in response.json()
    response_json = response.json()
    assert response_json["detail"][0]["loc"] == ["query", "text"]
    assert response_json["detail"][0]["msg"] == "Field required"


def test_retrieve_data_invalid_n_results():
    query_text = "test"
    response = client.get(
        "/api/retrieve_data", params={"text": query_text, "n_results": "invalid"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "detail" in response.json()
    response_json = response.json()
    assert response_json["detail"][0]["loc"] == ["query", "n_results"]
    assert (
        response_json["detail"][0]["msg"]
        == "Input should be a valid integer, unable to parse string as an integer"
    )


def test_retrieve_data_non_existent_data():
    text_content = "This is a test document"
    client.post(
        "/api/ingest_text", data=text_content, headers={"Content-Type": "text/plain"}
    )

    response = client.get(
        "/api/retrieve_data",
        params={
            "text": "non-existent",
            "filename": "non-existent.pdf",
            "user": "non-existent",
            "date": "2099-12-31",
            "n_results": 1,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert "documents" in response.json()
    assert len(response.json()["documents"]) == 0


def test_delete_data_from_chromadb():
    with open("app/tests/data/test.pdf", "rb") as f:
        client.post("/api/ingest_file", files={"file": f})

        params: dict = {"file_name": "test.pdf"}

        response = client.delete("/api/delete_data", params=params)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": "Data deleted successfully."}


def test_load_data():
    test_data = [
        {
            "question": "What is FastAPI?",
            "answer": "FastAPI is a modern web framework for Python.",
            "doc": "FastAPI Introduction",
            "url": "http://fastapi.tiangolo.com/"
        },
        {
            "question": "What is Chroma DB?",
            "answer": "Chroma DB is a vector database for AI and embeddings.",
            "doc": "Chroma Documentation",
            "url": "http://chroma.com/docs/"
        }
    ]

    response = client.post("/api/faq/load_records", json=test_data)
    assert response.status_code == 201
    assert response.json().get("status") == 201

    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.json() == {
        "status": "HEALTHY",
        "mongodb": "HEALTHY",
        "chromadb": "HEALTHY",
    }


def test_delete_one_question():
    test_data = [
        {
            "question": "Who is Zmyshenko Valerii Albertovich? 148854 test",
            "answer": "Pls delete me",
            "doc": "FastAPI Introduction",
            "url": "http://fastapi.tiangolo.com/"
        }
    ]

    response = client.post("/api/faq/load_records", json=test_data)
    assert response.status_code == 201
    assert response.json().get("status") == 201
    response = client.request(
        method="DELETE",
        url="/api/common/delete_one_chroma_record",
        json={
            "collection_name": "faq",
            "filter":
            {
                "question": test_data[0]["question"]
            }
        }
    )

    assert response.status_code == 200
    assert response.json().get("status") == 200


def test_random_questions():
    rand = 2
    queries = [{"collection": "faq", "random": rand}]
    response = client.post("/api/faq/random_questions", json=queries)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == len(queries)


def test_similar_questions():
    queries = [{"search": "What is FastAPI?", "collection": "faq", "top": 1, "similarity": 0.985}]
    response = client.post("/api/faq/similar_questions", json=queries)
    assert response.status_code == 200
    results = response.json()
    assert len(results) > 0


def test_webscraper():
    url = "https://www.stuba.sk/sk/zahranicne-partnerske-institucie.html?page_id=204"
    response = client.post(
        "/api/webscraper/webscraper",
        json={"url": url},
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == 200
    assert len(response.json()["data"]) > 0
