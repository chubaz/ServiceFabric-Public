import os
import httpx
import json
from datetime import datetime
from functools import wraps

class FabricSDK:
    """
    Standard Python SDK for Service Fabric Gateway interaction.
    Allows Flask/Django services to notify the central hub of events.
    """
    def __init__(self, service_slug=None):
        self.service_slug = service_slug or os.getenv('SERVICE_SLUG', 'unknown_service')
        self.gateway_url = os.getenv('GATEWAY_INTERNAL_URL', 'http://fastapi_core:8000')
        self.api_prefix = os.getenv('GATEWAY_API_PREFIX', '/api/v1')

    def broadcast(self, event_type: str, data: dict = {}):
        """
        Sends a synchronous broadcast request to the Gateway.
        """
        try:
            payload = {
                "event": event_type,
                "data": data,
                "source": self.service_slug,
                "timestamp": datetime.utcnow().isoformat()
            }
            with httpx.Client(timeout=2.0) as client:
                response = client.post(f"{self.gateway_url}/broadcast", json=payload)
                return response.status_code == 200
        except Exception as e:
            print(f"[FabricSDK] Broadcast failed: {e}")
            return False

    def notify_on_change(self, event_name=None):
        """
        Decorator to automatically broadcast an event when a function returns successfully.
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                result = f(*args, **kwargs)
                # If the function succeeded (didn't raise), broadcast
                name = event_name or f"{self.service_slug}_updated"
                self.broadcast(name, {"action": f.__name__})
                return result
            return decorated_function
        return decorator

    @property
    def vector_store(self):
        return VectorStoreInterface(self.gateway_url)

class VectorStoreInterface:
    def __init__(self, gateway_url):
        self.url = f"{gateway_url}/vector"

    def ingest(self, collection: str, documents: list[str], metadatas: list[dict], ids: list[str]):
        try:
            payload = {
                "collection": collection,
                "documents": documents,
                "metadatas": metadatas,
                "ids": ids
            }
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(f"{self.url}/ingest", json=payload)
                return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def search(self, collection: str, query: str, top_k: int = 3, metadata_filter: dict = None):
        try:
            payload = {
                "collection": collection,
                "query": query,
                "top_k": top_k,
                "filter": metadata_filter
            }
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(f"{self.url}/search", json=payload)
                return resp.json()
        except Exception as e:
            return {"error": str(e)}

# Shared instance
fabric = FabricSDK()
