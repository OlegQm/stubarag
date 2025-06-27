from typing import Dict, Any, List

from app.mcp.tools.chromadb_get_webscrapes import ChromaDBGetWebScrapesTool
from app.mcp.tools.mongodb_search_knowledge import MongoDBSearchKnowledgeTool

class MCPClient:
    def __init__(self):
        self._tools = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the MCP client and all tools."""
        if self._initialized:
            return

        self._tools["chromadb"] = ChromaDBGetWebScrapesTool()
        self._tools["mongodb"] = MongoDBSearchKnowledgeTool()

        for tool in self._tools.values():
            await tool.initialize()

        self._initialized = True

    async def close(self) -> None:
        """Close all tool connections."""
        for tool in self._tools.values():
            await tool.close()

    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get a list of available tools for OpenAI."""
        tool_configs = []

        for tool in self._tools.values():
            tool_configs.append(tool.get_tool_config())

        return tool_configs
        
    async def call_tool(
        self,
        tool_name: str,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a specific tool directly."""
        if tool_name not in self._tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        return await self._tools[tool_name].execute(args)

mcp_client = MCPClient()
