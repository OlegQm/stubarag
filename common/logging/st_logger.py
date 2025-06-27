import os
from streamlit import logger as st_log

from common.logging import setup_logger

"""

A module that instantiates project-wide global logger for streamlit-based apps.

"""

# Create a logger instance for streamlit-based apps and modules
st_logger = st_log.get_logger("streamlit")

# Set up loggers formatting
setup_logger.set_logger_formatting(st_logger)

# Enable debug mode if the DEBUG_MODE environment variable is set
#   DEBUG_MODE=1 -> debug mode enabled
#   DEBUG_MODE=0 -> debug mode disabled
if os.getenv("DEBUG_MODE") == "1":
    setup_logger.enable_debug_mode(st_logger)