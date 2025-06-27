from typing import Dict, Any
from fastapi import HTTPException

from app.routers.schemas import ToolCallResponse
from app.mcp.client import mcp_client

async def call_tool_service(
    name: str,
    args: Dict[str, Any]
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
    try:
        return ToolCallResponse(
            tool_response = await mcp_client.call_tool(tool_name=name, args=args)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from ValueError
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {e}"
        ) from Exception
