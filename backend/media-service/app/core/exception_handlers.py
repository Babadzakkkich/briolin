from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import MediaServiceException
from app.core.logger import logger

async def media_exception_handler(request: Request, exc: MediaServiceException):
    if exc.status_code >= 500:
        logger.error(f"Media service exception: {exc.message}", exc_info=True)
    else:
        logger.warning(f"Media service exception: {exc.message}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )

async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, MediaServiceException):
        return await media_exception_handler(request, exc)
    
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )