import random
import string
from typing import Optional
import redis.asyncio as redis
from datetime import timedelta

from app.core.config import settings
from app.core.logger import logger


class VerificationService:
    """Сервис для управления кодами верификации email в Redis"""
    
    def __init__(self):
        self.redis_client = None
    
    async def _get_redis(self):
        """Получить соединение с Redis (ленивая инициализация)"""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(
                f"redis://{settings.redis.host}:{settings.redis.port}/{settings.redis.db}",
                decode_responses=True,
                encoding="utf-8"
            )
        return self.redis_client
    
    def generate_code(self, length: int = 6) -> str:
        """Сгенерировать 6-значный код верификации"""
        return ''.join(random.choices(string.digits, k=length))
    
    async def save_verification_code(self, email: str, code: str, expires_minutes: int = 15) -> bool:
        """Сохранить код верификации в Redis с TTL"""
        try:
            redis_client = await self._get_redis()
            key = f"email_verification:{email.lower()}"
            await redis_client.setex(key, timedelta(minutes=expires_minutes), code)
            logger.info(f"Verification code saved for {email}, expires in {expires_minutes} minutes")
            return True
        except Exception as e:
            logger.error(f"Failed to save verification code for {email}: {e}")
            return False
    
    async def get_verification_code(self, email: str) -> Optional[str]:
        """Получить код верификации из Redis"""
        try:
            redis_client = await self._get_redis()
            key = f"email_verification:{email.lower()}"
            code = await redis_client.get(key)
            return code
        except Exception as e:
            logger.error(f"Failed to get verification code for {email}: {e}")
            return None
    
    async def verify_code(self, email: str, code: str) -> bool:
        """Проверить код верификации"""
        saved_code = await self.get_verification_code(email)
        if saved_code and saved_code == code:
            await self.delete_verification_code(email)
            logger.info(f"Email {email} verified successfully")
            return True
        logger.warning(f"Invalid verification code for {email}")
        return False
    
    async def delete_verification_code(self, email: str) -> bool:
        """Удалить код верификации"""
        try:
            redis_client = await self._get_redis()
            key = f"email_verification:{email.lower()}"
            await redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete verification code for {email}: {e}")
            return False


# Singleton
_verification_service = None


def get_verification_service() -> VerificationService:
    global _verification_service
    if _verification_service is None:
        _verification_service = VerificationService()
    return _verification_service