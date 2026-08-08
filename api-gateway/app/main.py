from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.middleware.auth_middleware import AuthMiddleware
from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import GatewayException
from app.core.exception_handlers import gateway_exception_handler, global_exception_handler
from app.api.v1.endpoints import router as api_router
from app.websocket.routes import router as ws_router
from app.websocket.proxy import get_websocket_proxy


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Briolin API Gateway...")

    yield

    # Graceful shutdown
    logger.info("Shutting down API Gateway...")

    # Закрываем все WebSocket соединения
    try:
        ws_proxy = get_websocket_proxy()
        await ws_proxy.shutdown()
    except Exception as e:
        logger.error(f"Error during WebSocket shutdown: {e}")

    logger.info("API Gateway shutdown complete")


app = FastAPI(
    title="Briolin API Gateway",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.gateway.debug else None,
    redoc_url="/redoc" if settings.gateway.debug else None,
)

# Регистрируем обработчики исключений
app.add_exception_handler(GatewayException, gateway_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Порядок важен: CORS должен оборачивать остальные middleware, чтобы браузер
# видел CORS-заголовки даже при 401 от AuthMiddleware.
app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.gateway.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API роуты (REST)
app.include_router(api_router, prefix="/api/v1")

# WebSocket роуты
app.include_router(ws_router)


@app.get("/health")
async def health_check():
    """Health check с информацией о WebSocket"""
    ws_proxy = get_websocket_proxy()
    ws_stats = ws_proxy.get_stats()

    return {
        "status": "healthy",
        "service": "api-gateway",
        "timestamp": datetime.utcnow().isoformat(),
        "websocket": {
            "active_connections": ws_stats["active_connections"],
            "target": ws_stats["chat_service_target"],
        },
    }


@app.get("/")
async def root():
    return {
        "message": "Briolin API Gateway",
        "version": "1.0.0",
        "docs": "/docs" if settings.gateway.debug else None,
        "websocket_endpoint": "/ws",
    }