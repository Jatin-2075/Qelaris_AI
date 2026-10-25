from fastapi import FastAPI

from platform_backend.app.routers.incident_router import router as incident_router


app = FastAPI(
    title="Sentinel Platform API",
    version="0.1.0",
)

app.include_router(incident_router)