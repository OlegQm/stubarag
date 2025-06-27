import logging

import pymongo
from fastapi.responses import JSONResponse
from requests.exceptions import RequestException

from app.routers.schemas import Page
from app.services.webscraper.webscraper_batch_service import extract_pages_content
from app.database import mongo_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def refresh_records() -> None:
    """
    Refreshes records in the specified MongoDB collection
    and sends URLs for processing.

    Args:
        refresh_collection (str): The name of the collection to refresh.

    Returns:
        None
    """
    refresh_collection = "webscraper"

    if not refresh_collection.strip():
        raise ValueError(
            "Invalid collection name: must be a non-empty string."
        )

    try:
        refresh_collection = mongo_db.get_or_create_collection(
            refresh_collection,
            ("url", pymongo.ASCENDING),
            ("version", pymongo.DESCENDING)
        )

        urls = refresh_collection.find({}, {"_id": 0, "url": 1})
        urls_list = [Page(url=doc["url"]) for doc in urls if "url" in doc]

        if not urls_list:
            logging.info("No URLs found to refresh.")
            return

        response = await extract_pages_content(urls_list)

        if isinstance(response, JSONResponse) and response.status_code == 200:
            logging.info(response.body.decode("utf-8"))
        else:
            raise Exception(
                "Unexpected response type or status from extract_pages_content."
            )

    except (ValueError, KeyError, TypeError, RequestException) as e:
        logging.error(f"Error during record refresh: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise
