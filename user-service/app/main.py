from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import logger
from app.database.session import dispose_engine, engine
from app.database.models import Base
from app.core.exceptions import UserServiceException
from app.core.exception_handlers import user_exception_handler, global_exception_handler
from app.api.v1 import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting User Service...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    logger.info("Shutting down User Service...")
    await dispose_engine()

app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None
)

# Регистрируем обработчики исключений
app.add_exception_handler(UserServiceException, user_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}