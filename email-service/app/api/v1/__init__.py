from fastapi import APIRouter
from app.api.v1 import email

router = APIRouter()
router.include_router(email.router)