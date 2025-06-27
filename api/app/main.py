from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.cron_jobs.refresh_pages_job import refresh_records
from app.routers.faq import (
    random_questions,
    similar_questions,
    load_faq_data
)
from app.routers import (
    delete_embeddings,
    ingest,
    status,
    vector_search
)
from app.routers.webscraper import (
    webscraper,
    webscraper_batch,
    get_chunks
)
from app.routers.common import (
    clear_chroma_collection,
    clear_mongo_collection,
    delete_one_mongo_record,
    delete_one_chroma_record,
    get_mongo_records,
    drop_chroma_collection,
    drop_mongo_collection
)
from app.routers.testing import (
    delete_mongo_records as testers_delete_mongo_records,
    get_mongo_records as testers_get_mongo_records,
    upload_qna as testers_upload_records,
    # start_llm_test
)
from app.routers.mcp import (
    call_tool,
    get_available_tools
)
from app.mcp.client import mcp_client

"""
This module initializes and configures the FastAPI application for the project.

It sets up the main FastAPI app instance with custom documentation URLs and includes
various API routers for different functionalities such as status checks, data ingestion,
vector search, and deletion of embeddings.

Routers:
- status: Handles status check endpoints.
- ingest: Manages data ingestion endpoints.
- vector_search: Provides endpoints for vector-based search operations.
- delete_embeddings: Manages endpoints for deleting embeddings.
- clear_chroma_collection: Clears the Chroma collection.
- clear_mongo_collection: Clears the MongoDB collection.
- delete_one_mongo_record: Deletes a single record from MongoDB by filter.
- delete_one_chroma_record: Deletes a single record from Chroma by filter.
- get_mongo_records: Returns a single or multiple records by filter.
- drop_chroma_collection: Permanently deletes a ChromaDB collection.
- drop_mongo_collection: Permanently deletes a MongoDB collection.
- random_questions: Provides random FAQ questions from `faq` collection.
- similar_questions: Provides similar to `search` FAQ questions from `faq` collection.
- load_faq_data: Loads data in `faq` collection.
- webscraper: Manages web scraping operations.
- webscraper_batch: Manages batch web scraping operations.
- get_chunks: Retrieves chunks of data from specific webpage.
- testers_delete_mongo_records: Deletes multiple records from the MongoDB 'qna' collection based on a specified filter.
- testers_get_mongo_records: Retrieves one or more records from the MongoDB 'qna' collection using a specified filter.
- testers_upload_records: Uploads a set of question-and-answer pairs to the MongoDB 'qna' collection for testing purposes.
- start_llm_test (CURRENTLY UNAVAILABLE): Initiates a test LLM to validate its functionality and performance.
- call_tool: Calls an external tool via MCP.
- get_available_tools: Lists available tools via MCP.

The main application is accessible with the base URL `/api`, and the documentation
can be accessed at `/api/docs` for Swagger UI, `/api/redoc` for ReDoc, and `/api/openapi.json`
for the OpenAPI schema.

"""

##### CRON JOBS #####

@asynccontextmanager
async def lifespan(app: FastAPI):
    await mcp_client.initialize()
    scheduler = AsyncIOScheduler()
    trigger = CronTrigger(day_of_week="sun", hour=0, minute=0)
    scheduler.add_job(refresh_records, trigger)
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)
    await mcp_client.close()

##### ENDPOINTS #####

app = FastAPI(
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)
api_router = APIRouter(prefix="/api")

# Basic endpoints
api_router.include_router(status.router)
api_router.include_router(ingest.router)
api_router.include_router(vector_search.router)
api_router.include_router(delete_embeddings.router)

# Common
api_router.include_router(clear_chroma_collection.router)
api_router.include_router(clear_mongo_collection.router)
api_router.include_router(delete_one_mongo_record.router)
api_router.include_router(delete_one_chroma_record.router)
api_router.include_router(get_mongo_records.router)
api_router.include_router(drop_chroma_collection.router)
api_router.include_router(drop_mongo_collection.router)

# FAQ
api_router.include_router(random_questions.router)
api_router.include_router(similar_questions.router)
api_router.include_router(load_faq_data.router)

# Webscraper
api_router.include_router(webscraper.router)
api_router.include_router(webscraper_batch.router)
api_router.include_router(get_chunks.router)

# Tests
api_router.include_router(testers_delete_mongo_records.router)
api_router.include_router(testers_get_mongo_records.router)
api_router.include_router(testers_upload_records.router)
# api_router.include_router(start_llm_test.router)

# MCP
api_router.include_router(call_tool.router)
api_router.include_router(get_available_tools.router)

app.include_router(api_router)
