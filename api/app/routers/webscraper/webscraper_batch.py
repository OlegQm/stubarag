from typing import List

from fastapi import APIRouter, Body

from app.routers.schemas import WebScraperResponse, Page
from app.services.webscraper.webscraper_batch_service import extract_pages_content

router = APIRouter()

@router.post(
    "/webscraper/webscraper_batch",
    response_model=WebScraperResponse
)
async def webscraper(
    pages: List[Page] = Body(...)
) -> WebScraperResponse:
    """
    Asynchronously scrapes web pages and processes their content.

    Args:
        pages (List[Page]): A list of Page objects containing the URL, description,
        and owner information for each page to be scraped.

    Returns:
        WebScraperResponse: The response object containing the results of the web scraping operation.
    """
    return await extract_pages_content(pages)
