from typing import Dict, Any, List
import json
import asyncio
import time
import os

import pytest
from httpx import (
    BasicAuth,
    AsyncClient,
    Timeout,
    RequestError
)
from openai import OpenAI
from .conftest import results

from src.api.services.get_rag_answer_service import send_query

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") or "your_api_key")

BASE_URL_API = os.getenv("BASE_URL") or "http://backend:8080"
SENSE_TEST_THRESHOLD = 16 / 27
_TESTER_DATA = os.getenv("REVERSE_PROXY_TESTER") or "your_password"
if ":" not in _TESTER_DATA:
    raise ValueError(
        "Environment variable 'REVERSE_PROXY_TESTER' must " \
        "contain username and password separated by a colon."
    )
_USERNAME, _PASSWORD = map(str.strip, _TESTER_DATA.split(":"))

async def ask_bot(question: str, role: str = "user") -> str:
    """
    Sends a question to a bot and retrieves its response.

    Args:
        question (str): The question or message to send to the bot.
        role (str, optional): The role of the sender (e.g., "user", "system"). Defaults to "user".

    Returns:
        str: The bot's response as a string. If an error occurs, returns an error message.

    Raises:
        RequestError: If there is an issue with the request to the bot.
        ValueError: If the response format is invalid.
        KeyError: If a required key is missing in the response.
    """
    payload = [
        {
            "role": role,
            "content": question + "If you need to write a person's name, " +
            "write in the format: title (if there is one), then first name, then last name."
        }
    ]
    try:
        response = await send_query(
            conversation_content=payload,
            needs_enhancement=True
        )
        return 200, response.answer.strip()
    except RequestError as e:
        return 500, "error: " + str(e)
    except (ValueError, KeyError) as e:
        return 500, "error: invalid response format - " + str(e)


def ask_openai(question: str, role: str = "system") -> str:
    """
    Sends a question to the OpenAI API and retrieves the response.

    Args:
        question (str): The question or prompt to send to the OpenAI API.
        role (str, optional): The role of the message sender. Defaults to "system".
            Common roles include "system", "user", and "assistant".

    Returns:
        str: The content of the response message from the OpenAI API, stripped of leading
        and trailing whitespace.

    Raises:
        openai.error.OpenAIError: If there is an issue with the API request or response.
    """
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": role, "content": question}]
    )
    return response.choices[0].message.content.strip()


async def load_questions(payload_filter: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Asynchronously fetches a list of questions and their corresponding answers
    from a remote API based on the provided filter.

    Args:
        payload_filter (Dict[str, Any]): A dictionary containing filter criteria
            to be applied when fetching the records.

    Returns:
        List[Dict[str, str]]: A list of dictionaries where each dictionary maps
            a question to its corresponding answer.

    Raises:
        pytest.fail: If the response does not contain records or if an error
            occurs during the request.

    Notes:
        - The function uses Basic Authentication to access the API.
        - The API endpoint is expected to return a JSON response with a "records"
          key containing the data.
        - If an error occurs during the request or processing, the function
          fails the test using `pytest.fail`.
    """
    try:
        auth = BasicAuth(
            username=_USERNAME,
            password=_PASSWORD
        )
        async with AsyncClient(auth=auth, timeout=Timeout(60.0, connect=10.0)) as http_client:
            response = await http_client.request(
                method="GET",
                url=f"{BASE_URL_API}/api/testing/get_records",
                content=json.dumps({"filter": payload_filter}),
                headers={"Content-Type": "application/json"}
            )
        response.raise_for_status()
        data_dict = response.json()
        if not data_dict or "records" not in data_dict:
            pytest.fail("No records found in the response.")
            return []
        records = data_dict["records"]
        return [{row["question"]: row["answer"]} for row in records]
    except RequestError as e:
        pytest.fail(f"Error requesting questions and answers: {e}")
        return []
    except Exception as e:
        pytest.fail(f"Exception appeared: {e}")
        return []


############ TEST CASES ############


@pytest.mark.dependency(name="test_ask_openai_no_exceptions_and_returns_string")
def test_ask_openai_no_exceptions_and_returns_string():
    """
    Verify that ask_openai does not raise exceptions and returns a string.
    """
    try:
        resp = ask_openai("Hello, world!")
    except Exception as e:
        pytest.fail(f"ask_openai raised an exception: {e}")
    assert isinstance(resp, str)
    assert resp.strip() != ""


@pytest.mark.asyncio
@pytest.mark.dependency(
    name="test_bot_response_format",
    depends=["test_ask_openai_no_exceptions_and_returns_string"]
)
@pytest.mark.parametrize("question", ["Kto je dekan?"])
async def test_bot_response_format(question):
    """
    Tests whether the ask_bot function returns
        a properly formatted string without errors.

    Args:
        question (str): A test question for the bot.
    """
    status, response = await ask_bot(question)
    assert isinstance(response, str)
    assert status == 200


@pytest.mark.asyncio
@pytest.mark.dependency(depends=["test_bot_response_format"])
@pytest.mark.parametrize("question", ["Kto je dekan?"])
async def test_bot_response_time(question):
    """
    Measures and validates that the bot's
        response time is within acceptable limits.

    Args:
        question (str): A test question to measure response time.
    """
    start_time = time.time()
    await ask_bot(question)
    duration = time.time() - start_time
    assert duration <= 20


@pytest.mark.asyncio
@pytest.mark.dependency(
    name="test_concurrent_ask_bot",
    depends=["test_bot_response_format"]
)
async def test_concurrent_ask_bot():
    """
    Run several concurrent requests to the bot
    and verify that none of them fail and all responses are strings without the "error" prefix.
    """
    questions = [f"Question {i}?" for i in range(5)]
    responses = await asyncio.gather(
        *(ask_bot(q) for q in questions),
        return_exceptions=True
    )

    assert len(responses) == len(questions)

    for idx, resp in enumerate(responses):
        if isinstance(resp, Exception):
            pytest.fail(f"ask_bot raised exception on question #{idx}: {resp}")
        status, answer = resp
        assert 200 <= status < 300, f"Bad status on #{idx}: {status}"
        assert isinstance(answer, str), f"Response #{idx} is not a string: {answer!r}"
        assert not answer.lower().startswith("Failed"), f"Response #{idx} contains error"


@pytest.mark.asyncio
@pytest.mark.dependency(
    name="test_contains_key_data",
    depends=["test_bot_response_format"]
)
async def test_contains_key_data():
    flt = {"pattern_or_llm": "pattern"}
    data = await load_questions(flt)
    if not data:
        pytest.fail("No data loaded for testing.")

    correct_counter = 0

    for row in data:
        question, correct_answer = list(row.items())[0]
        _, answer = await ask_bot(question)

        idx = answer.find("---")
        if idx == -1:
            idx = len(answer)
        answer_lower = answer.lower()[:idx]

        is_test_correct = 1 if correct_answer.lower() in answer_lower else 0
        correct_counter += is_test_correct

        results.append({
            question: (
                f"Bot's answer: {answer}\n"
                f"Correct answer: {correct_answer}\n"
                "Answer was " + ("in" if not is_test_correct else "")
                + "valid"
            )
        })

    assert correct_counter > 0 and correct_counter >= len(data) * SENSE_TEST_THRESHOLD


@pytest.mark.asyncio
@pytest.mark.dependency(depends=["test_contains_key_data"])
async def test_answer_validity():
    """
    Validates correctness of the bot's answers
        by comparing them with OpenAI's GPT-4o-mini.
    """
    filter = {
        "pattern_or_llm": "llm"
    }

    data = await load_questions(filter)
    if not data:
        pytest.fail("No data loaded for testing.")

    valid_counter = 0

    for row in data:
        question, correct_answer = list(row.items())[0]
        _, answer = await ask_bot(question)
        validation_request = (
            f"I asked my bot question '{question}', correct answer '{correct_answer}', "
            f"and got bot answer '{answer}'. Check if the correct answer is contained "
            "in the bot's answer (at least on 95%), and if so, write only 'YES', and if not, write only 'NO'."
        )
        validation_answer = ask_openai(validation_request).strip().upper()
        valid_counter += 1 if "YES" in validation_answer else 0
        results.append(
            {
                question: (
                    f"Bot's answer: {answer}\n" +
                    f"Correct answer: {correct_answer}\n" +
                    "Answer was " +
                    ("in" if "NO" in validation_answer else "") +
                    "valid"
                )
            }
        )

    assert valid_counter > 0
