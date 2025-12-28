from fastapi import APIRouter
from .auth import router as auth_router
from .internal import router as internal_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(internal_router)