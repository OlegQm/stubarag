from typing import Dict, Any

from app.database import mongo_db

from bson import ObjectId, Binary
from datetime import datetime


class MongoDBSearchKnowledgeTool:
    def __init__(self):
        self._client = mongo_db
        self._collection = None
        self._initialized = False

    async def initialize(self):
        """Initialize the MongoDB 'knowledge' collection."""
        if self._initialized:
            return
        self._collection = self._client.get_or_create_collection("knowledge")
        self._initialized = True

    async def close(self):
        """Close the MongoDB connection."""
        if self._client:
            self._client.close()

    def get_tool_config(self) -> Dict[str, Any]:
        """Get the tool configuration for OpenAI API."""
        return {
            "type": "function",
            "function": {
                "name": "mongodb",
                "description": "Query or modify data in MongoDB",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "description": "The operation to perform",
                            "enum": ["find", "find_one", "count"]
                        },
                        "filter": {
                            "type": "object",
                            "description": "Filter criteria for the operation"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of documents to return"
                        },
                        "sort": {
                            "type": "object",
                            "description": "Sort criteria for find operations"
                        }
                    },
                    "required": ["operation"]
                }
            }
        }

    def _encode_mongo_document(self, doc):
        """
        Recursively encodes a MongoDB document into JSON-serializable types.

        This method traverses the input document, converting special MongoDB types
        such as ObjectId, Binary, and datetime into string representations suitable
        for JSON serialization. It handles nested dictionaries and lists.

        Args:
            doc: The MongoDB document or value to encode. Can be a dict, list, ObjectId,
                 Binary, datetime, bytes, or any other type.

        Returns:
            The encoded document or value, with all MongoDB-specific types converted
            to JSON-serializable representations.
        """
        if isinstance(doc, dict):
            return {k: self._encode_mongo_document(v) for k, v in doc.items()}
        elif isinstance(doc, list):
            return [self._encode_mongo_document(item) for item in doc]
        elif isinstance(doc, ObjectId):
            return str(doc)
        elif isinstance(doc, Binary):
            import base64
            return base64.b64encode(doc).decode('ascii')
        elif isinstance(doc, datetime):
            return doc.isoformat()
        elif isinstance(doc, bytes):
            import base64
            return base64.b64encode(doc).decode('ascii')
        else:
            return doc

    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a MongoDB operation."""
        operation = args.get("operation")
        filter_dict = args.get("filter", {})
        limit = args.get("limit", 0)
        sort = args.get("sort", None)

        if not operation:
            return {"error": "Operation is required"}

        if operation == "find":
            cursor = self._collection.find(filter_dict)

            if limit > 0:
                cursor = cursor.limit(limit)
            if sort:
                cursor = cursor.sort([(k, v) for k, v in sort.items()])
                
            results = []
            for doc in cursor:
                doc = self._encode_mongo_document(doc=doc)
                results.append(doc)
                
            return {"results": results}

        elif operation == "find_one":
            result = self._collection.find_one(filter_dict)
            if result:
                result = self._encode_mongo_document(result)
            return {"result": result}

        elif operation == "count":
            count = self._collection.count_documents(filter_dict)
            return {"count": count}

        else:
            return {"error": f"Operation '{operation}' is not supported"}
