import logging

"""

A module for setting up global loggers.

"""

def setup_streamhandler():
    """
    Sets up a stream handler for logging with a specific format.

    The stream handler outputs log messages to the console. The log messages
    include the timestamp, log level, module name, function name, and the 
    actual log message. The timestamp is formatted as 'day-month-year hour:minute:second'.

    Args:
        None

    Returns:
        - logging.StreamHandler: Configured stream handler with the specified formatter.

    """

    # Create a console handler
    stream_handler = logging.StreamHandler()

    # Create a formatter that uses the correct format for date
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(module)s:%(funcName)s -> %(message)s', datefmt='%d-%m-%Y %H:%M:%S')

    # Set the formatter for the handler
    stream_handler.setFormatter(formatter)

    return stream_handler


def set_logger_formatting(logger):
    """
    Sets up the logger formatting by adding configured streamhandler 
    to logger instance.

    Args:
        None

    Returns:
        None

    """

    # Get set up stream handler
    stream_handler = setup_streamhandler()

    # Remove default streamlit stream handler from the streamlit logger
    if hasattr(logger, "streamlit_console_handler"):
        logger.removeHandler(logger.streamlit_console_handler)

    # Add the handler to the logger
    logger.addHandler(stream_handler)


def enable_debug_mode(logger):
    """
    Enables debug mode for the loggers.

    This function sets the log level to DEBUG
    if debug mode is enabled.

    Args:
        None

    Returns:
        None

    """

    # Set the log level to DEBUG for both loggers
    logger.setLevel(logging.DEBUG)