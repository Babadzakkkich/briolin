import hmac
from typing import Optional
from fastapi import HTTPException, Request

from .config import settings


class RequestSecurity:
    """
    Дополнительная безопасность для проверки запросов между сервисами
    """
    
    @staticmethod
    def create_signature(token: str) -> str:
        """
        Создает HMAC подпись для токена
        """
        return hmac.new(
            settings.shared.jwt_secret.encode(),
            token.encode(),
            'sha256'
        ).hexdigest()
    
    @staticmethod
    def verify_signature(token: str, signature: str) -> bool:
        """
        Проверяет HMAC подпись токена
        """
        expected_signature = RequestSecurity.create_signature(token)
        return hmac.compare_digest(signature, expected_signature)
    
    @staticmethod
    def verify_request(request: Request) -> tuple[dict, str]:
        """
        Проверяет запрос и возвращает пользователя и оригинальный токен
        """
        internal_token = request.headers.get("x-internal-token")
        signature = request.headers.get("x-token-signature")
        
        if not internal_token or not signature:
            raise HTTPException(
                status_code=401,
                detail="Missing authentication headers"
            )
        
        # Проверяем подпись
        if not RequestSecurity.verify_signature(internal_token, signature):
            raise HTTPException(
                status_code=401,
                detail="Invalid token signature"
            )
        
        # Дальше токен проверяется в get_current_user
        return internal_token


request_security = RequestSecurity()