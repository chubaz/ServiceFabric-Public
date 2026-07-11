import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.api.dependencies.auth import verify_fabric_token
from app.core.config import settings
from app.security.principal import PrincipalContext
from app.services.background_tasks import audit_log_event
from app.services.http_client import http_client

router = APIRouter()


@router.get("/dashboard-data")
async def get_dashboard_data(
    background_tasks: BackgroundTasks,
    principal: PrincipalContext = Depends(verify_fabric_token),
):
    """Fetch dashboard sources for a verified caller without retaining its credential."""
    client = http_client.get_client()
    background_tasks.add_task(
        audit_log_event,
        "FabricGateway",
        "dashboard_accessed",
        {"principal_subject": principal.subject, "principal_type": principal.principal_type},
    )

    flask_req = client.get(f"{settings.FLASK_SERVICE_URL}/")
    django_req = client.get(f"{settings.DJANGO_SERVICE_URL}/api/")

    try:
        flask_res, django_res = await asyncio.gather(flask_req, django_req, return_exceptions=True)
        return {
            "orchestrated": True,
            "flask_data": flask_res.json()
            if not isinstance(flask_res, Exception) and flask_res.status_code == 200
            else "Unavailable",
            "django_data": django_res.json()
            if not isinstance(django_res, Exception) and django_res.status_code == 200
            else "Unavailable",
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Upstream orchestration failed") from exc
