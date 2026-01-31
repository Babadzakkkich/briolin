from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import TestingException
from app.core.logger import logger

async def testing_exception_handler(request: Request, exc: TestingException):
    """Обработчик для всех TestingException"""
    if exc.status_code >= 500:
        logger.error(f"Testing exception: {exc.message}", exc_info=True)
    else:
        logger.warning(f"Testing exception: {exc.message}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )

async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик для всех исключений"""
    if isinstance(exc, TestingException):
        return await testing_exception_handler(request, exc)
    
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )