# HOW TO LOG


In our project, we log using python default `logging` module.

## Non-streamlit apps and modules
In non-streamlit apps and modules, add this import:

`from common.logging.global_logger import logger`

In your functions, use e. g. `logger.info("log message")`

## Streamlit apps and modules
In streamlit apps and modules, add this import:

```from common.logging.st_logger import st_logger```

In your functions, use e. g. `st_logger.info("log message")`

## Log level

**Default logging level is INFO.**

Please choose an appropriate level for your logs:


-  `logger.debug()` for auxiliary prints during debugging.
-  `logger.info()` for monitoring program general flow.
-  `logger.warning()` for warnings.
-  `logger.error()` for errors.
-  `logger.critical()` when app execution must be stopped or interrupted.

**! Choose wisely !**

## Debug mode

Default logging level is INFO. If you want to use auxiliary prints with log
level DEBUG, please enable **DEBUG_MODE** environmental variable in docker compose.

Valid **DEBUG_MODE** states:

- `DEBUG_MODE=1` -> debug mode is enabled.
- `DEBUG_MODE=0` -> debug mode is disabled.

**Debug mode is disabled for all containers by default !**
