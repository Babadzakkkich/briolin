from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from shared.auth.jwt import jwt_manager
from app.core.logger import logger

router = APIRouter(prefix="/debug", tags=["Debug"])

security = HTTPBearer(auto_error=False)

@router.get("/token-status")
async def token_status(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Статус текущего внутреннего токена"""
    token = request.headers.get("x-internal-token")
    
    if not token:
        return {"status": "no_token", "message": "No internal token found"}
    
    try:
        info = jwt_manager.get_token_info(token)
        
        return {
            "status": "valid" if info.get("valid") else "expired",
            "expires_at": info.get("expires_at").isoformat() if info.get("expires_at") else None,
            "time_left_seconds": info.get("time_left_seconds"),
            "user": info.get("user"),
            "created": info.get("created_at").isoformat() if info.get("created_at") else None,
            "token_preview": f"{token[:20]}...{token[-20:]}" if len(token) > 40 else token
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/auth-headers")
async def auth_headers(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Показывает заголовки аутентификации"""
    headers = {}
    for key, value in request.headers.items():
        if key.lower().startswith(('authorization', 'x-internal', 'x-token')):
            if 'token' in key.lower() and len(value) > 30:
                headers[key] = f"{value[:30]}..."
            else:
                headers[key] = value
    
    return {
        "headers": headers,
        "client_ip": request.client.host if request.client else None,
        "path": request.url.path
    }