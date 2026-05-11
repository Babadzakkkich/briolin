from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import MatchingServiceException
from app.core.logger import logger


async def matching_exception_handler(request: Request, exc: MatchingServiceException):
    if exc.status_code >= 500:
        logger.error(f"Matching service exception: {exc.message}", exc_info=True)
    else:
        logger.warning(f"Matching service exception: {exc.message}")

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, MatchingServiceException):
        return await matching_exception_handler(request, exc)

    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )