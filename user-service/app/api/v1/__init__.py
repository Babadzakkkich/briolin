from fastapi import APIRouter
from .users import router as users_router
from .internal import router as internal_router

router = APIRouter()
router.include_router(users_router)
router.include_router(internal_router)