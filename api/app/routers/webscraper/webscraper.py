from fastapi import APIRouter, Body

from app.routers.schemas import WebScraperResponse, Page
from app.services.webscraper.webscraper_service import extract_page_content

router = APIRouter()

@router.post(
    "/webscraper/webscraper",
    response_model=WebScraperResponse
)
async def webscraper(
    page: Page = Body(...)
) -> WebScraperResponse:
    """
    Web scraping endpoint to extract static content from a given web page.

    Args:
        pages (List[Page]): A list of Page objects containing the URL, description,
        and owner information for each page to be scraped.

    Returns:
        WebScraperResponse: The response containing the extracted data 
        or an error message if the extraction fails.
    """
    return await extract_page_content(page.url, page.description, page.owner)
