from typing import Dict, List, Tuple

import pymongo
from fastapi import status
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError, DuplicateKeyError
from pymongo.collection import Collection as MongoCollection

from app.database import mongo_db
from app.routers.schemas import UploadQNAResponse


def return_response_in_upload_qna_format(
    message: str,
    http_status: int
) -> JSONResponse:
    """
    Constructs and returns a JSONResponse object in the Upload QnA format.

    Args:
        message (str): The message to include in the response.
        http_status (int): The HTTP status code for the response.

    Returns:
        JSONResponse: A JSON response containing the status and message in the Upload QnA format.
    """
    response_data = UploadQNAResponse(status=http_status, message=message)
    return JSONResponse(
        content=response_data.model_dump(),
        status_code=http_status
    )


def process_qna_entries(
    collection: MongoCollection,
    qna: Dict[str, Dict[str, str]],
    session
) -> Tuple[int, int, int, List[str], List[str]]:
    """
    Process each QnA entry: validate, insert, update, and count duplicates.
    Returns inserted_count, updated_count, duplicate_count, invalid_rows, duplicate_questions.
    """
    inserted_count = 0
    updated_count = 0
    duplicate_count = 0
    invalid_rows: List[str] = []
    duplicate_questions: List[str] = []

    for question, info in qna.items():
        if not isinstance(question, str) or not question.strip():
            invalid_rows.append(
                f"Question '{question}' is not a valid non-empty string."
            )
            continue
        if not isinstance(info, dict) or not (1 <= len(info) <= 2):
            invalid_rows.append(
                f"Question '{question}' info must be a dict with 1-2 keys."
            )
            continue
        if not all(k in ["pattern", "llm"] for k in info.keys()):
            invalid_rows.append(
                f"For question '{question}', keys must be 'pattern' and/or 'llm'."
            )
            continue
        if not all(isinstance(v, str) for v in info.values()):
            invalid_rows.append(
                f"For question '{question}', all values must be strings."
            )
            continue

        for key in ["pattern", "llm"]:
            new_answer = info.get(key, "").strip()
            if not new_answer:
                continue

            existing = collection.find_one(
                {"question": question, "pattern_or_llm": key},
                session=session
            )
            if existing:
                if existing.get("answer") != new_answer:
                    collection.update_one(
                        {"_id": existing["_id"]},
                        {"$set": {"answer": new_answer}},
                        session=session
                    )
                    updated_count += 1
                else:
                    duplicate_questions.append(f"{question} ({key})")
                    duplicate_count += 1
                continue

            try:
                res = collection.insert_one(
                    {
                        "question": question,
                        "answer": new_answer,
                        "pattern_or_llm": key
                    },
                    session=session
                )
                if res.acknowledged:
                    inserted_count += 1
                else:
                    invalid_rows.append(
                        f"Question '{question}' failed to insert."
                    )
            except DuplicateKeyError:
                duplicate_questions.append(f"{question} ({key})")
                duplicate_count += 1

        if (
            not info.get("pattern", "").strip()
            and not info.get("llm", "").strip()
        ):
            invalid_rows.append(
                f"Both 'pattern' and 'llm' for question '{question}' are empty."
            )

    return (
        inserted_count,
        updated_count,
        duplicate_count,
        invalid_rows,
        duplicate_questions
    )


async def upload_data(
    qna: Dict[str, Dict[str, str]]
) -> JSONResponse:
    """9
    Uploads QnA data to the database, processing insertions, updates, and deletions.

    Args:
        qna (Dict[str, Dict[str, str]]): A dictionary where each key is a question, 
            and the value is another dictionary containing keys like "pattern" or "llm" 
            with corresponding string values.

    Returns:
        JSONResponse: A response object containing the status of the operation, 
            including counts of inserted, updated, deleted, and duplicate entries, 
            as well as any errors or duplicate questions encountered.

    Raises:
        PyMongoError: If a database error occurs during the operation.

    Notes:
        - The function validates the input to ensure it is a non-empty dictionary.
        - It uses a MongoDB collection to store the QnA data, ensuring unique entries 
          based on the combination of "question" and "pattern_or_llm".
        - The function performs the following operations:
            - Inserts new entries.
            - Updates existing entries.
            - Deletes entries not present in the input.
            - Tracks duplicate and invalid rows.
        - If there are invalid rows or duplicates, the response status is set to 
          HTTP 206 Partial Content; otherwise, it is HTTP 200 OK.
    """
    if not isinstance(qna, dict) or not qna:
        return return_response_in_upload_qna_format(
            message="Invalid input: 'qna' must be a non-empty dictionary.",
            http_status=status.HTTP_400_BAD_REQUEST
        )

    collection = mongo_db.get_or_create_collection(
        "qna",
        ("question", pymongo.ASCENDING),
        ("pattern_or_llm", pymongo.ASCENDING),
        unique=True
    )

    inserted_count = 0
    updated_count = 0
    duplicate_count = 0
    all_invalid_rows: List[str] = []
    all_duplicate_questions: List[str] = []
    deleted_count = 0

    try:
        with mongo_db.client.start_session() as session:
            with session.start_transaction():
                ins, upd, dup, invalid_rows, dup_qs = process_qna_entries(
                    collection, qna, session
                )
                inserted_count += ins
                updated_count += upd
                duplicate_count += dup
                all_invalid_rows.extend(invalid_rows)
                all_duplicate_questions.extend(dup_qs)

                wanted = [
                    {"question": q, "pattern_or_llm": key}
                    for q, info in qna.items()
                    for key in ("pattern", "llm")
                    if info.get(key, "").strip()
                ]
                if wanted:
                    res = collection.delete_many(
                        {"$nor": wanted}, session=session
                    )
                    deleted_count = res.deleted_count
    except PyMongoError as e:
        return return_response_in_upload_qna_format(
            message=f"Database error: {e}",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    if all_invalid_rows or duplicate_count > 0:
        status_code = status.HTTP_206_PARTIAL_CONTENT
    else:
        status_code = status.HTTP_200_OK

    parts = [f"Inserted: {inserted_count}\nUpdated: {updated_count}\nDeleted: {deleted_count}\nDuplicates: {duplicate_count}\n"]
    if all_duplicate_questions:
        parts.append(
            "Existing duplicates:\n" + "\n".join(all_duplicate_questions)
        )
    if all_invalid_rows:
        parts.insert(0, "Errors:\n" + "\n".join(all_invalid_rows) + "\n")
    final_message = "\n\n".join(parts)

    return return_response_in_upload_qna_format(
        message=final_message,
        http_status=status_code
    )
