from fastapi import APIRouter

from app.routers.schemas import AvailableToolsResponse
from app.services.mcp.get_available_tools_service import available_tools_service

router = APIRouter()

@router.get(
    "/mcp/get_available_tools",
    response_model=AvailableToolsResponse
)
async def get_tools() -> AvailableToolsResponse:
    """
    Asynchronously retrieves the available tools.

    Returns:
        AvailableToolsResponse:
            The response containing the list of available tools.
    """
    return await available_tools_service()
