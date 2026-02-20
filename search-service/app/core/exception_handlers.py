from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import SearchServiceException
from app.core.logger import logger


async def search_exception_handler(request: Request, exc: SearchServiceException):
    """Обработчик для всех SearchServiceException"""
    if exc.status_code >= 500:
        logger.error(f"Search service exception: {exc.message}", exc_info=True)
    else:
        logger.warning(f"Search service exception: {exc.message}")

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик для всех исключений"""
    if isinstance(exc, SearchServiceException):
        return await search_exception_handler(request, exc)

    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )