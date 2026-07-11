import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from app.api.dependencies.auth import require_service_scope, verify_fabric_token, verify_websocket_principal
from app.security.principal import PrincipalContext

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            await connection.send_text(message)


manager = ConnectionManager()


@router.post("/broadcast")
async def broadcast_event(
    payload: dict,
    principal: PrincipalContext = Depends(verify_fabric_token),
):
    require_service_scope(principal, "fabric:broadcast")
    message = json.dumps(
        {
            "event": payload.get("event", "unknown_event"),
            "data": payload.get("data", {}),
            "source": principal.subject,
            "timestamp": payload.get("timestamp", ""),
        }
    )
    await manager.broadcast(message)
    return {"status": "broadcasted", "event": payload.get("event", "unknown_event")}


@router.websocket("/ws/events/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    principal = await verify_websocket_principal(websocket)
    if principal is None:
        return

    await manager.connect(websocket)
    try:
        await websocket.send_text(f"Welcome Client {client_id}! Connected to Fabric Gateway.")
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                message = json.dumps(
                    {
                        "event": payload.get("event", "client_event"),
                        "data": payload.get("data", {}),
                        "source": principal.subject,
                        "timestamp": payload.get("timestamp", ""),
                    }
                )
                await manager.broadcast(message)
            except (json.JSONDecodeError, AttributeError):
                await manager.broadcast(f"Event from {principal.subject}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
