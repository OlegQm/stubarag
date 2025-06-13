def start_tests():
    """
    Remove this function when tests uncommented.
    """
    pass

# from typing import List, Dict, Optional
# import asyncio

# import pytest
# import pymongo
# from fastapi.responses import JSONResponse

# import app.llm_tests.llm_test_main as test_llm
# from app.routers.schemas import TestsResponse
# from app.database import mongo_db
# from app.services.testing.upload_qna_service import get_latest_release

# class CaptureLogPlugin:
#     def __init__(self):
#         """
#         Initializes the CaptureLogPlugin with an empty log list.
#         """
#         self.logs = []

#     def pytest_runtest_logreport(self, report):
#         """
#         Captures the log report from pytest during the 'call' phase.
        
#         Args:
#             report: The pytest report object.
#         """
#         if report.when == 'call':
#             self.logs.append(f"{report.nodeid}: {report.outcome}")

# def return_response_in_tests_format(
#     message: str,
#     http_status: int,
#     custom_results: List[Dict[str, str]],
#     pytest_log: str
# ) -> JSONResponse:
#     """
#     Constructs and returns a JSONResponse object formatted for test results.

#     Args:
#         message (str): A descriptive message about the test result.
#         http_status (int): The HTTP status code to include in the response.
#         custom_results (List[Dict[str, str]]): A list of custom result dictionaries containing additional test details.
#         pytest_log (str): The log output from pytest to include in the response.

#     Returns:
#         JSONResponse: A JSON response object containing the formatted test results.
#     """
#     response_data = TestsResponse(
#         message=message,
#         status=http_status,
#         custom_results=custom_results,
#         pytest_log=pytest_log
#     )
#     return JSONResponse(
#         content=response_data.model_dump(),
#         status_code=http_status
#     )

# async def start_tests() -> JSONResponse:
#     """
#     Asynchronously starts the execution of LLM-related tests and processes the results.

#     This function clears previous test results, executes the tests using pytest, and logs the output.
#     It computes a summary of valid test responses based on custom results by counting the number of answers that differ
#     from "answer was invalid". It retrieves the latest release information from the database and archives the test results 
#     along with the pytest logs and a test summary in the archive_tests collection. If no release is found in the qna collection,
#     a partial response is returned.

#     Returns:
#         JSONResponse: A JSON response containing the status of the operation, test results, pytest logs, and a test summary.

#     Raises:
#         Exception: If any error occurs during the execution of the tests or database operations.
#     """
#     try:
#         test_llm.results.clear()
#         log_plugin = CaptureLogPlugin()

#         await asyncio.to_thread(
#             pytest.main,
#             ["app/llm_tests/llm_test_main.py", "-q"],
#             plugins=[log_plugin]
#         )

#         custom_results = test_llm.results
#         pytest_log = "\n".join(log_plugin.logs)
#         valid_count = sum(1 for item in custom_results for answer in item.values() if answer != "answer was invalid")
#         total_count = len(custom_results)
#         test_summary = f"{valid_count}/{total_count}"

#         qna_collection = mongo_db.get_or_create_collection(
#             "qna",
#             ("question", pymongo.ASCENDING),
#             ("pattern_or_llm", pymongo.ASCENDING),
#             unique=True
#         )
#         release: Optional[str] = get_latest_release(qna_collection)
#         if release is None:
#             return return_response_in_tests_format(
#                 ("Operation completed successfully but 'qna' collection is empty and it's not possible to add the test results to the archive"),
#                 206,
#                 custom_results,
#                 pytest_log
#             )
#         archive_collection = mongo_db.get_or_create_collection(
#             "archive_tests",
#             ("release", pymongo.ASCENDING),
#             unique=True
#         )

#         archive_collection.replace_one(
#             {"release": release},
#             {
#                 "release": release,
#                 "custom_results": custom_results,
#                 "pytest_log": pytest_log,
#                 "test_summary": test_summary
#             },
#             upsert=True
#         )

#         return return_response_in_tests_format(
#             "Operation completed successfully",
#             200,
#             custom_results,
#             pytest_log
#         )
#     except Exception as e:
#         return return_response_in_tests_format(
#             f"Error: {e}",
#             500,
#             [],
#             ""
#         )
