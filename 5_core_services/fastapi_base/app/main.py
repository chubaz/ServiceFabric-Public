from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.endpoints import health, orchestration, websockets, vector
from app.services.http_client import http_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize shared HTTPX client
    http_client.get_client()
    yield
    # Shutdown: Close client safely
    await http_client.close_client()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/openapi.json",
    root_path=settings.API_V1_STR,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(orchestration.router, prefix="/orchestration", tags=["Orchestration"])
app.include_router(vector.router, prefix="/vector", tags=["Vector Store"])
app.include_router(websockets.router, tags=["Real-Time"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Service Fabric Central API"}
