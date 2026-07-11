from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List

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
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@router.post("/broadcast")
async def broadcast_event(payload: dict):
    """
    Allows non-websocket services (like Flask/Django) to broadcast events.
    """
    event = payload.get("event", "unknown_event")
    data = payload.get("data", {})
    source = payload.get("source", "system")
    
    import json
    message = json.dumps({
        "event": event,
        "data": data,
        "source": source,
        "timestamp": payload.get("timestamp", "")
    })
    
    await manager.broadcast(message)
    return {"status": "broadcasted", "event": event}

@router.websocket("/ws/events/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        # Send an initial welcome message
        await websocket.send_text(f"Welcome Client {client_id}! Connected to Fabric Gateway.")
        while True:
            # Wait for any messages from the frontend
            data = await websocket.receive_text()
            
            try:
                import json
                payload = json.loads(data)
                event = payload.get("event", "client_event")
                event_data = payload.get("data", {})
                
                # Re-broadcast in the standard structured format
                message = json.dumps({
                    "event": event,
                    "data": event_data,
                    "source": client_id,
                    "timestamp": payload.get("timestamp", "")
                })
                await manager.broadcast(message)
            except (json.JSONDecodeError, AttributeError):
                # Fallback for non-JSON or malformed messages
                await manager.broadcast(f"Event from {client_id}: {data}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client {client_id} disconnected.")
