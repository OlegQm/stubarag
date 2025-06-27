from typing import Dict, Any

from fastapi import APIRouter, Body

from app.routers.schemas import ToolCallResponse
from app.services.mcp.call_tool_service import call_tool_service

router = APIRouter()

@router.post(
    "/mcp/call_tool",
    response_model=ToolCallResponse
)
async def call_tool(
    name: str = Body(..., embed=True),
    args: Dict[str, Any] = Body(..., embed=True)
) -> ToolCallResponse:
    """
    Calls a specified tool via the MCP client with provided arguments.

    Args:
        name (str): The name of the tool to call.
        args (Dict[str, Any]): Arguments to pass to the tool.

    Returns:
        ToolCallResponse: The response from the tool call.

    Raises:
        HTTPException: If the tool call fails or invalid parameters are provided.
    """
    return await call_tool_service(
            name=name,
            args=args
        )
