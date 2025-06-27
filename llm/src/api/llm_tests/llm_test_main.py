from typing import Dict, Any, List, Tuple
import json
import time
import os
import re
import math
import asyncio
from tenacity import (
    retry,
    wait_random_exponential,
    stop_after_attempt,
    retry_if_exception_type
)

import pytest
from httpx import (
    BasicAuth,
    AsyncClient,
    Timeout,
    RequestError
)
from openai import AsyncOpenAI, RateLimitError
from aiolimiter import AsyncLimiter

from src.api.llm_tests.conftest import results
from src.api.services.get_rag_answer_service import send_query

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY") or "your_api_key")
openai_rate_limiter = AsyncLimiter(60, 60)
send_query_limiter = AsyncLimiter(30, 60)

BASE_URL_API = os.getenv("BASE_URL") or "http://backend:8080"
SENSE_TEST_THRESHOLD = 0.5
_TESTER_DATA = os.getenv("REVERSE_PROXY_TESTER") or "your_password"
if ":" not in _TESTER_DATA:
    raise ValueError(
        "Environment variable 'REVERSE_PROXY_TESTER' must "
        "contain username and password separated by a colon."
    )
_USERNAME, _PASSWORD = map(str.strip, _TESTER_DATA.split(":"))

NO_DATA_PHRASES = [
    "ospravedlňujem sa", "prepáč", "bohužiaľ",
    "nemám žiadne údaje", "nemám údaje",
    "nemám žiadne informácie", "nemám informác",
    "nemám k dispozícii", "neviem určiť",
    "neviem presne určiť", "nie je uveden",
    "nie je v dostupnom kontexte uvedený",
    "v kontexte nie je", "nemám uveden",
    "nie je explicitne uveden",
    "unfortunately", "i cannot determine",
    "i apologize", "i am sorry", "i could not find",
    "i cannot find", "i do not know",
    "i do not have any data", "i do not have any information",
    "nemám k tomu informácie", "nemám k tomu údaje",
    "nemám žiadnu odpoveď", "odpoveď nie je dostupná",
    "odpoveď nie je známa", "neviem odpovedať",
    "neviem na to odpovedať", "neviem poskytnúť informácie",
    "neviem poskytnúť údaje", "neviem zistiť",
    "neviem povedať", "nie sú dostupné informácie",
    "nie sú dostupné údaje", "nie je známe",
    "nie je možné zistiť", "nie je možné určiť",
    "nie je k dispozícii", "nie je k tomu informácia",
    "nie je k tomu údaj", "nie je odpoveď",
    "no data available", "no information available",
    "no answer available", "no answer found",
    "no relevant data", "no relevant information",
    "cannot answer", "cannot provide information",
    "cannot provide data", "cannot determine",
    "unable to answer", "unable to determine",
    "unable to find", "unable to provide information",
    "unable to provide data", "not available",
    "not enough information", "not enough data",
    "not specified", "not mentioned",
    "not found in the context", "not present in the context",
    "not provided", "not listed",
    "žiadne informácie", "žiadne údaje",
    "žiadna odpoveď", "žiadna informácia nie je dostupná",
    "žiadny údaj nie je dostupný",
    "nie je v dostupných zdrojoch špecifikovaný"
]

def is_number(s: str) -> bool:
    """
    Check if the given string represents a number (integer or float, with optional sign).

    Args:
        s (str): The string to check.

    Returns:
        bool: True if the string is a valid number, otherwise False.
    """
    return bool(re.fullmatch(r"-?\d+([.,]\d+)?", s.strip()))

def contains_no_data_phrase(text: str) -> bool:
    """
    Check if any of the NO_DATA_PHRASES are present in the given text.

    Args:
        text (str): Text to search for no-data phrases.

    Returns:
        bool: True if any phrase is found in the text, otherwise False.
    """
    for phrase in NO_DATA_PHRASES:
        if re.search(r'\b{}\b'.format(re.escape(phrase)), text):
            return True
    return False

@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_random_exponential(min=0.5, max=8),
    stop=stop_after_attempt(6)
)
async def ask_bot(question: str, role: str = "user") -> Tuple[int, str]:
    """
    Ask a question to the bot asynchronously and return the status code and answer string.
    External calls are protected with a timeout to avoid hanging.

    Args:
        question (str): The question to ask.
        role (str, optional): The role context for the question. Defaults to "user".

    Returns:
        Tuple[int, str]: A tuple of (status_code, response_text).
            status_code 200 means OK, 504 means timeout, 500 means error.
    """
    payload = [
        {
            "role": role,
            "content": (
                question + "\n\n"
            )
        }
    ]
    try:
        async with send_query_limiter:
            response = await asyncio.wait_for(
                send_query(
                    conversation_content=payload,
                    needs_enhancement=False
                ),
                timeout=60
            )
        return 200, response.answer.strip()
    except asyncio.TimeoutError:
        return 504, "error: Timeout while waiting for bot response"
    except RequestError as e:
        return 500, "error: " + str(e)
    except (ValueError, KeyError) as e:
        return 500, "error: invalid response format - " + str(e)

@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_random_exponential(min=0.5, max=8),
    stop=stop_after_attempt(6)
)
async def ask_openai(question: str, role: str = "system") -> str:
    """
    Ask a question to the OpenAI API asynchronously and return the answer string.
    Protected by timeout.

    Args:
        question (str): The question to ask.
        role (str, optional): The role context for the question. Defaults to "system".

    Returns:
        str: The answer from OpenAI, or a timeout error string.
    """
    try:
        async with openai_rate_limiter:
            response = await asyncio.wait_for(
                openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": role, "content": question}]
                ),
                timeout=60
            )
        return response.choices[0].message.content.strip()
    except asyncio.TimeoutError:
        return "error: Timeout while waiting for OpenAI response"

async def load_questions(payload_filter: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Load a list of questions and answers from a remote API using given filters.
    Protected by timeout.

    Args:
        payload_filter (Dict[str, Any]): The filter for the API request.

    Returns:
        List[Dict[str, str]]: A list of dictionaries, each containing a question-answer pair.
    """
    try:
        auth = BasicAuth(
            username=_USERNAME,
            password=_PASSWORD
        )
        async with AsyncClient(auth=auth, timeout=Timeout(60.0, connect=10.0)) as http_client:
            response = await asyncio.wait_for(
                http_client.request(
                    method="GET",
                    url=f"{BASE_URL_API}/api/testing/get_records",
                    content=json.dumps({"filter": payload_filter}),
                    headers={"Content-Type": "application/json"}
                ),
                timeout=60
            )
        response.raise_for_status()
        data_dict = response.json()
        if not data_dict or "records" not in data_dict:
            pytest.fail("No records found in the response.")
            return []
        records = data_dict["records"]
        return [{row["question"]: row["answer"]} for row in records]
    except asyncio.TimeoutError:
        pytest.fail("Timeout while loading questions.")
        return []
    except RequestError as e:
        pytest.fail(f"Error requesting questions and answers: {e}")
        return []
    except Exception as e:
        pytest.fail(f"Exception appeared: {e}")
        return []

############ TEST CASES ############

@pytest.mark.asyncio
@pytest.mark.dependency(name="test_ask_openai_no_exceptions_and_returns_string")
async def test_ask_openai_no_exceptions_and_returns_string():
    """
    Test that ask_openai completes successfully and returns a non-empty string.

    Ensures the OpenAI API is available and returns a valid string without raising exceptions or timing out.
    """
    try:
        resp = await asyncio.wait_for(ask_openai("Hello, world!"), timeout=60)
    except asyncio.TimeoutError:
        pytest.fail("ask_openai timed out!")
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
    Test that ask_bot returns a properly formatted response.

    Checks that the bot returns a status code 200 and the response is a string for a basic question.
    """
    try:
        status, response = await asyncio.wait_for(ask_bot(question), timeout=60)
    except asyncio.TimeoutError:
        pytest.fail("ask_bot timed out!")
    assert isinstance(response, str)
    assert status == 200

@pytest.mark.asyncio
@pytest.mark.dependency(depends=["test_bot_response_format"])
@pytest.mark.parametrize("question", ["Kto je dekan?"])
async def test_bot_response_time(question):
    """
    Test that ask_bot responds within an acceptable time limit.

    Fails if the response time exceeds 20 seconds.
    """
    start_time = time.time()
    try:
        await asyncio.wait_for(ask_bot(question), timeout=60)
    except asyncio.TimeoutError:
        pytest.fail("ask_bot timed out!")
    duration = time.time() - start_time
    assert duration <= 20

@pytest.mark.asyncio
@pytest.mark.dependency(
    name="test_concurrent_ask_bot",
    depends=["test_bot_response_format"]
)
async def test_concurrent_ask_bot():
    """
    Test several parallel bot queries for robustness and correctness.

    Sends several questions to ask_bot in parallel with timeouts and checks that all responses are valid.
    """
    questions = [f"Question {i}?" for i in range(5)]
    tasks = [asyncio.wait_for(ask_bot(q), timeout=60) for q in questions]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    assert len(responses) == len(questions)
    for idx, resp in enumerate(responses):
        if isinstance(resp, Exception):
            pytest.fail(f"ask_bot raised exception on question #{idx}: {resp}")
        status, answer = resp
        assert 200 <= status < 300, f"Bad status on #{idx}: {status}"
        assert isinstance(answer, str), f"Response #{idx} is not a string: {answer!r}"
        assert not answer.lower().startswith("failed"), f"Response #{idx} contains error"

@pytest.mark.asyncio
@pytest.mark.dependency(
    name="test_contains_key_data",
    depends=["test_concurrent_ask_bot"]
)
async def test_contains_key_data():
    """
    Test if the bot correctly answers questions by comparing to expected answers.

    Loads a set of questions with correct answers and verifies that bot responses meet the required accuracy threshold.
    """
    flt = {"pattern_or_llm": "pattern"}
    try:
        data = await asyncio.wait_for(load_questions(flt), timeout=60)
    except asyncio.TimeoutError:
        pytest.fail("load_questions timed out!")
    if not data:
        pytest.fail("No data loaded for testing.")

    correct_counter = 0
    errors = []
    for row in data:
        question, correct_answer = list(row.items())[0]
        try:
            _, answer = await asyncio.wait_for(ask_bot(question), timeout=60)
        except asyncio.TimeoutError:
            pytest.fail(f"ask_bot timed out for question: {question}")
        assert answer.strip() != "", f"Empty answer for question: {question}"
        idx = answer.find("---")
        if idx == -1:
            idx = len(answer)
        answer_lower = answer.lower()[:idx]
        if is_number(correct_answer):
            pattern = r'\b{}\b'.format(re.escape(correct_answer.replace(',', '.')))
            is_test_correct = re.search(pattern, answer_lower.replace(',', '.')) is not None
        else:
            is_test_correct = correct_answer.lower() in answer_lower
        correct_counter += int(is_test_correct)
        if not is_test_correct:
            errors.append({
                "question": question,
                "answer": answer,
                "correct_answer": correct_answer
            })
        results.append({
            question: (
                f"Bot's answer: {answer}\n"
                f"Correct answer: {correct_answer}\n"
                + ("Answer was valid" if is_test_correct else "Answer was invalid")
                + ("\nN/A" if contains_no_data_phrase(answer_lower) else "")
            )
        })
    min_correct = math.ceil(len(data) * SENSE_TEST_THRESHOLD)
    assert correct_counter >= min_correct, f"Correct: {correct_counter}, Required: {min_correct}, Errors: {errors}"

@pytest.mark.asyncio
@pytest.mark.dependency(depends=["test_contains_key_data"])
async def test_answer_validity():
    """
    Validate the quality of the bot's answers using OpenAI as a judge.

    For each question, checks if the bot's answer is validated as correct by OpenAI, using a prompt that expects YES/NO/NO DATA.
    """
    filter = {"pattern_or_llm": "llm"}
    try:
        data = await asyncio.wait_for(load_questions(filter), timeout=60)
    except asyncio.TimeoutError:
        pytest.fail("load_questions timed out!")
    if not data:
        pytest.fail("No data loaded for testing.")
    valid_counter = 0
    errors = []
    for row in data:
        question, correct_answer = list(row.items())[0]
        try:
            _, answer = await asyncio.wait_for(ask_bot(question), timeout=60)
        except asyncio.TimeoutError:
            pytest.fail(f"ask_bot timed out for question: {question}")
        validation_request = (
            f"I asked my bot question: '{question}', correct answer is: '{correct_answer}', "
            f"and got bot's answer: '{answer}'. Check whether the bot's answer "
            "is correct answer or at least the part of the correct answer. "
            "If the bot's answer IS CORRECT answer or the bot's answer is at least"
            " similar to the correct answer, return only 'YES'. "
            "If the bot's answer DOES NOT contain the correct answer or data that is"
            " misleading, return only 'NO'. "
        )
        try:
            validation_answer = (await asyncio.wait_for(ask_openai(validation_request), timeout=60)).strip().upper()
        except asyncio.TimeoutError:
            pytest.fail(f"ask_openai timed out for question: {question}")
        if validation_answer == "YES":
            valid_counter += 1
        if validation_answer not in ("YES", "NO", "NO DATA"):
            errors.append({
                "question": question,
                "answer": answer,
                "correct_answer": correct_answer,
                "validation_answer": validation_answer
            })
        validation_answer_lower = validation_answer.lower()
        results.append(
            {
                question: (
                    f"Bot's answer: {answer}\n" +
                    f"Correct answer: {correct_answer}\n" +
                    ("Answer was valid" if validation_answer == "YES" else "Answer was invalid")
                    + ("\nN/A" if "no data" in validation_answer_lower else "")
                )
            }
        )
    assert valid_counter > 0, f"No valid answers found. Errors: {errors}"
