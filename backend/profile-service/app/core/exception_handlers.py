from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import ProfileServiceException
from app.core.logger import logger

async def profile_exception_handler(request: Request, exc: ProfileServiceException):
    """Обработчик для всех ProfileServiceException"""
    if exc.status_code >= 500:
        logger.error(f"Profile service exception: {exc.message}", exc_info=True)
    else:
        logger.warning(f"Profile service exception: {exc.message}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )

async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик для всех исключений"""
    if isinstance(exc, ProfileServiceException):
        return await profile_exception_handler(request, exc)
    
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )