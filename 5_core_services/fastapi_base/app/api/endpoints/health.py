from fastapi import APIRouter
router = APIRouter()

@router.get("/")
async def check_health():
    return {
        "status": "ok",
        "service": "fastapi_core",
        "message": "Fabric API Gateway is running smoothly."
    }
