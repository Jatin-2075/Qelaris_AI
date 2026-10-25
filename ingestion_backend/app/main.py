from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from .api.ingestion import router as ingestion_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Manage resources owned by the HTTP application."""
    yield


app = FastAPI(
    title="Sentinel Ingestion API",
    description="Receives telemetry events for asynchronous processing.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(ingestion_router, prefix="/v1")


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}