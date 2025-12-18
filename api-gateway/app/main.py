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

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Briolin API Gateway...")
    yield
    logger.info("Shutting down API Gateway...")

app = FastAPI(
    title="Briolin API Gateway",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.gateway.debug else None,
    redoc_url="/redoc" if settings.gateway.debug else None
)

# Регистрируем обработчики исключений
app.add_exception_handler(GatewayException, gateway_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth Middleware
app.add_middleware(AuthMiddleware)

# API роуты
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "api-gateway",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    return {
        "message": "Briolin API Gateway",
        "version": "1.0.0",
        "docs": "/docs" if settings.gateway.debug else None
    }