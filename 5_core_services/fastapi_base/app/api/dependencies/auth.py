from fastapi import Header, HTTPException, Security
from typing import Optional

async def verify_fabric_token(x_fabric_token: Optional[str] = Header(None)):
    """
    Dependency to verify internal requests between Fabric apps.
    In production, this would validate a JWT or check Redis.
    """
    if not x_fabric_token or x_fabric_token != "super-secret-fabric-key":
        raise HTTPException(status_code=403, detail="Invalid or missing Fabric Token")
    return x_fabric_token
