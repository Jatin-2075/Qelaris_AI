from fastapi import FastAPI

from platform_backend.app.routers.auth_router import router as auth_router
from platform_backend.app.routers.event_router import router as event_router
from platform_backend.app.routers.incident_router import router as incident_router
from platform_backend.app.routers.project_router import router as project_router


app = FastAPI(
    title="Sentinel Platform API",
    version="0.1.0",
)

app.include_router(incident_router)
app.include_router(auth_router)
app.include_router(project_router)
app.include_router(event_router)