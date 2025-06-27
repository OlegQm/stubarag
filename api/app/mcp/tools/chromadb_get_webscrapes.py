import asyncio
from typing import Dict, Any
from app.database import get_chromadb_client
from app.utils import initialize_embedding_function

class ChromaDBGetWebScrapesTool:
    def __init__(self):
        self._client = None
        self._collection_name = "webscraper"
        self._collection = None
        self._embedding_function = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize the ChromaDB client and collection."""
        if self._initialized:
            return
        max_retries = 5
        for i in range(max_retries):
            try:
                self._client = await anext(get_chromadb_client())
                await self._client.heartbeat()
                break
            except Exception as e:
                if i < max_retries - 1:
                    print(f"Failed to connect to ChromaDB, retrying in 5 seconds... ({e})")
                    await asyncio.sleep(5)
                else:
                    raise e
        self._embedding_function = initialize_embedding_function()
        self._collection = await self._client.get_or_create_collection(
            name=self._collection_name,
            embedding_function=self._embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
        self._initialized = True

    async def close(self):
        """Close the ChromaDB connection."""
        pass

    def get_tool_config(self) -> Dict[str, Any]:
        """Get the tool configuration for OpenAI API."""
        return {
            "type": "function",
            "function": {
                "name": "chromadb",
                "description": "Search for information in the ChromaDB vector database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["query", "stats"],
                            "description": "The operation to perform (query or get stats)"
                        },
                        "query": {
                            "type": "string",
                            "description": "The query to search for in the database (for query operation)"
                        },
                        "n_results": {
                            "type": "integer",
                            "description": "Number of results to return (for query operation)",
                            "default": 3
                        },
                        "filter": {
                            "type": "object",
                            "description": "Optional filter to apply to the search (for query operation)"
                        }
                    },
                    "required": ["operation"]
                }
            }
        }

    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an operation on ChromaDB."""
        operation = args.get("operation")
        
        if not operation:
            return {"error": "Operation is required"}
            
        try:
            if operation == "query":
                return await self._execute_query(args)
            elif operation == "stats":
                return await self._execute_stats()
            else:
                return {"error": f"Unknown operation '{operation}'"}
        except Exception as e:
            return {"error": f"Failed to execute {operation}: {str(e)}"}

    async def _execute_query(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a query operation."""
        query = args.get("query")
        n_results = args.get("n_results", 3)
        filter_dict = args.get("filter")
        
        if not query:
            return {"error": "Query is required for query operation"}

        try:
            query_args = {
                "query_texts": [query],
                "n_results": n_results
            }

            if filter_dict and len(filter_dict) > 0:
                query_args["where"] = filter_dict

            results = await self._collection.query(**query_args)
            
            print(f"ChromaDB raw results: {results}")

            return {
                "documents": results.get("documents", [[]])[0],
                "metadatas": results.get("metadatas", [[]])[0],
                "distances": results.get("distances", [[]])[0],
                "ids": results.get("ids", [[]])[0]
            }
            
        except Exception as e:
            print(f"ChromaDB query error: {str(e)}")
            return {"error": f"Query failed: {str(e)}"}

    async def _execute_stats(self) -> Dict[str, Any]:
        """Get statistics about the ChromaDB database."""
        try:
            count = await self._collection.count()
            collections = [c.name for c in await self._client.list_collections()]
            
            return {
                "count": count,
                "collections": collections
            }
        except Exception as e:
            return {"error": f"Failed to get stats: {str(e)}"}
