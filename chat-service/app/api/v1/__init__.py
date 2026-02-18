from fastapi import APIRouter
from .chats import router as chats_router

router = APIRouter()
router.include_router(chats_router)