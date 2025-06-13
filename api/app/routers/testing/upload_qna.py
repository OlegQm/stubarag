from typing import Dict

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

from app.services.testing.upload_qna_service import upload_data

router = APIRouter()

@router.post(
    "/testing/upload_records"
)
async def upload_qna(
    qna: Dict[str, Dict[str, str]] = Body(..., embed=True)
) -> JSONResponse:
    """
    Endpoint to upload QnA data.

    This endpoint accepts a JSON body containing a dictionary where the keys are questions 
    (as strings) and the values are lists of strings (containing at least two elements: the answer 
    and an indicator for pattern or LLM). Additionally, a release identifier is provided. 
    The function validates the input, processes the data, and inserts the records into a MongoDB 
    collection using transactions. In case of partial success, the response message will include 
    information about the questions that already exist.

    Parameters:
        qna (Dict[str, List[str]]): A dictionary mapping questions to a list containing the answer 
            and a flag or indicator for pattern/LLM. The input must be provided in a JSON body with the key 'qna'.
        release (str): A string indicating the release version or identifier, provided in the JSON body 
            with the key 'release'.

    Returns:
        JSONResponse: A JSON response conforming to the UploadQNAResponse schema, containing the status 
        code and a message indicating the result of the upload operation.
    """
    return await upload_data(
        qna=qna
    )
