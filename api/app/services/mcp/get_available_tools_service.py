from fastapi import HTTPException

from app.routers.schemas import AvailableToolsResponse
from app.mcp.client import mcp_client

async def available_tools_service() -> AvailableToolsResponse:
    """
    Asynchronously retrieves the available tools.

    Returns:
        ToolCallResponse:
            The response containing the list of available tools.
    """
    try:
        return AvailableToolsResponse(
            tools_list = await mcp_client.get_available_tools()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {e}"
        ) from Exception
