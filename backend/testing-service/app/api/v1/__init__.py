from fastapi import APIRouter
from .tests import router as tests_router

router = APIRouter()
router.include_router(tests_router)