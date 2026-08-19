from fastapi import APIRouter
from .profiles import router as profiles_router
from .internal import router as internal_router

router = APIRouter()
router.include_router(profiles_router)
router.include_router(internal_router)