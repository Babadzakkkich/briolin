from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .profiles import router as profiles_router
from .tests import router as testing_router
from .chats import router as chats_router
from .search import router as search_router
from .media import router as media_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(users_router)
router.include_router(profiles_router)
router.include_router(testing_router)
router.include_router(chats_router)
router.include_router(search_router)
router.include_router(media_router)