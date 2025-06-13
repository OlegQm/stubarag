import os
import logging

from common.logging import setup_logger

"""

A module that instantiates project-wide global logger.

"""

# Create a logger instance for project-wide logging
logger = logging.getLogger("global_logger")

# Set up loggers formatting
setup_logger.set_logger_formatting(logger)

# Enable debug mode if the DEBUG_MODE environment variable is set
#   DEBUG_MODE=1 -> debug mode enabled
#   DEBUG_MODE=0 -> debug mode disabled
if os.getenv("DEBUG_MODE") == "1":
    setup_logger.enable_debug_mode(logger)