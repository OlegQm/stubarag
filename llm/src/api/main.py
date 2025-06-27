from fastapi import APIRouter, FastAPI

from src.api.routers import get_rag_answer

app = FastAPI(
    docs_url="/llm/docs",
    redoc_url="/llm/redoc",
    openapi_url="/llm/openapi.json"
)
api_router = APIRouter(prefix="/llm")

# Interaction with LLM
api_router.include_router(get_rag_answer.router)

app.include_router(api_router)
