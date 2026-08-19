from fastapi import APIRouter
from .matching import router as matching_router
from .internal import router as internal_router

router = APIRouter()
router.include_router(matching_router)
router.include_router(internal_router)