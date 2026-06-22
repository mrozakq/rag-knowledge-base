import os
from fastapi import Header, HTTPException

_API_KEY = os.environ.get("API_KEY", "")


async def require_api_key(authorization: str = Header(default="")):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization format, expected: Bearer <token>")
    token = parts[1]
    if not _API_KEY:
        raise HTTPException(status_code=500, detail="API_KEY not configured on server")
    if token != _API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
