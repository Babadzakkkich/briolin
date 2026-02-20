from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import GatewayException
from app.core.logger import logger

async def gateway_exception_handler(request: Request, exc: GatewayException):
    """Обработчик для всех GatewayException"""
    if exc.status_code >= 500:
        logger.error(f"Gateway exception: {exc.detail}", exc_info=True)
    else:
        logger.warning(f"Gateway exception: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик для всех исключений"""
    # Если это уже GatewayException, пропускаем
    if isinstance(exc, GatewayException):
        return await gateway_exception_handler(request, exc)
    
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )