from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import health, orchestration, vector, websockets
from app.core.config import settings
from app.services.http_client import http_client


class RequestSizeLimitMiddleware:
    """Reject oversized HTTP bodies without consuming the downstream request stream."""

    def __init__(self, app, max_body_size: int):
        self.app = app
        self.max_body_size = max_body_size

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        content_length = headers.get(b"content-length")
        if content_length and int(content_length) > self.max_body_size:
            await self._send_too_large(send)
            return

        received = 0

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_body_size:
                    raise RequestBodyTooLarge
            return message

        try:
            await self.app(scope, limited_receive, send)
        except RequestBodyTooLarge:
            await self._send_too_large(send)

    @staticmethod
    async def _send_too_large(send):
        await send({"type": "http.response.start", "status": 413, "headers": [(b"content-type", b"application/json")]})
        await send({"type": "http.response.body", "body": b'{"detail":"Request body exceeds the permitted size"}'})


class RequestBodyTooLarge(Exception):
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    http_client.get_client()
    yield
    await http_client.close_client()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/openapi.json",
    root_path=settings.API_V1_STR,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_middleware(RequestSizeLimitMiddleware, max_body_size=settings.MAX_REQUEST_BODY_BYTES)

app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(orchestration.router, prefix="/orchestration", tags=["Orchestration"])
app.include_router(vector.router, prefix="/vector", tags=["Vector Store"])
app.include_router(websockets.router, tags=["Real-Time"])


@app.get("/")
async def root():
    return {"message": "Welcome to the Service Fabric Central API"}
