from fastapi import APIRouter
from .matching import router as matching_router

router = APIRouter()
router.include_router(matching_router)