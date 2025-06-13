import tiktoken
import time
from functools import wraps
# TODO - temporary fix to avoid streamlit in requirements.txt
from common.logging.global_logger import logger as st_logger
from common.logging.global_logger import logger


"""

A module of custom function decorators for logging and monitoring.

"""


def count_tokens(func: callable) -> callable:
    """
    A decorator that counts and logs the number of tokens in the input and output
    of the decorated function.

    At the moment works only for OpenAI models.

    It is assumed that the first positional argument of decorated function is the 
    user query (input) and second is the llm client (llm).

    Args:
        - func (callable): The function to be decorated.

    Returns:
        - callable: The wrapped function with token counting and logging functionality.

    Logs:
        - Input token count
        - Output token count
        - Total token count (sum of input and output tokens)

    """
    @wraps(func)
    def count_tokens(*args, **kwargs):
        # Extract input from the function arguments
        # Assuming `input` is the first positional argument
        user_query = args[0]
        llm_model = args[1].model_name

        enc = tiktoken.encoding_for_model(llm_model)

        input_text = user_query
        input_tokens = enc.encode(input_text)
        input_token_count = len(input_tokens)
        st_logger.info(
            f"{func.__name__} - Input token count: {input_token_count}")
        # Call the original function
        response = func(*args, **kwargs)

        # Tokenize the response (assuming response is a string)
        output_tokens = enc.encode(response)
        output_token_count = len(output_tokens)
        st_logger.info(
            f"{func.__name__} - Output token count: {output_token_count}")
        # Log total tokens used
        total_tokens = input_token_count + output_token_count
        st_logger.info(f"{func.__name__} - Total token count: {total_tokens}")

        return response

    return count_tokens


def http_timer(func):
    """
    A decorator that logs the time taken for an HTTP request to complete.

    This decorator measures the time taken by the decorated function to execute
    and logs the elapsed time in seconds using the `st_logger`.

    Decorated function must be an asynchronous function.

    Args:
        func (callable): The function to be decorated.

    Returns:
        callable: The wrapped function with timing and logging functionality.

    """
    @wraps(func)
    async def http_timer(*args, **kwargs):
        # Record the start time before calling the function
        start_time = time.time()

        # Call the original function
        response = await func(*args, **kwargs)

        # Record the end time after the function has completed
        end_time = time.time()

        # Calculate the elapsed time in seconds
        elapsed_time = end_time - start_time

        # Log the elapsed time using st_logger with 8 decimal places precision
        st_logger.info(
            f"{func.__name__} - Request took {elapsed_time:.8f} seconds")

        # Return the response from the original function
        return response
    return http_timer


def callable_timer(func):
    """
    A decorator that measures the execution time of a function and logs it.

    Args:
        - func (callable): The function to be decorated.
    Returns:
        - callable: The wrapped function that includes timing and logging.
    Usage:
        @timer
        def my_function():
            # Function implementation

    """
    @wraps(func)
    def callable_timer(*args, **kwargs):
        # Record the start time before calling the function
        start_time = time.time()

        # Call the original function
        response = func(*args, **kwargs)

        # Record the end time after the function has completed
        end_time = time.time()

        # Calculate the elapsed time in seconds
        elapsed_time = end_time - start_time

        # Log the elapsed time using st_logger with 8 decimal places precision
        logger.info(
            f"{func.__name__} - Callable run took {elapsed_time:.8f} seconds")

        # Return the response from the original function
        return response
    return callable_timer
