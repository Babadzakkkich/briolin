from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import AuthException
from app.core.logger import logger

async def auth_exception_handler(request: Request, exc: AuthException):
    """Обработчик для всех AuthException"""
    if exc.status_code >= 500:
        logger.error(f"Auth exception: {exc.message}", exc_info=True)
    else:
        logger.warning(f"Auth exception: {exc.message}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )

async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик для всех исключений"""
    # Если это уже AuthException, пропускаем
    if isinstance(exc, AuthException):
        return await auth_exception_handler(request, exc)
    
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )