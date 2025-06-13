from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.services.testing.start_llm_test_service import start_tests

router = APIRouter()

@router.get("/testing/start_llm_test")
async def run_tests() -> JSONResponse:
    """
    Asynchronously starts and executes a series of tests using pytest, capturing their results and logs.

    Returns:
        JSONResponse: An object containing the custom test results and the pytest log output.
    """
    return await start_tests()
