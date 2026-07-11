from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
import asyncio
from app.services.http_client import http_client
from app.services.background_tasks import audit_log_event
from app.api.dependencies.auth import verify_fabric_token
from app.core.config import settings

router = APIRouter()

@router.get("/dashboard-data")
async def get_dashboard_data(
    background_tasks: BackgroundTasks, 
    token: str = Depends(verify_fabric_token) # DI Security Guard
):
    """
    Fetches data concurrently and triggers a background audit log.
    Protected by the verify_fabric_token dependency.
    """
    client = http_client.get_client()
    
    # 1. Trigger the background task (does NOT block the response)
    background_tasks.add_task(audit_log_event, "FabricGateway", "dashboard_accessed", {"token_used": token})

    # 2. Async Orchestration
    flask_req = client.get(f"{settings.FLASK_SERVICE_URL}/")
    django_req = client.get(f"{settings.DJANGO_SERVICE_URL}/api/")

    try:
        flask_res, django_res = await asyncio.gather(flask_req, django_req, return_exceptions=True)
        
        return {
            "orchestrated": True,
            "flask_data": flask_res.json() if not isinstance(flask_res, Exception) and flask_res.status_code == 200 else "Unavailable",
            "django_data": django_res.json() if not isinstance(django_res, Exception) and django_res.status_code == 200 else "Unavailable",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
