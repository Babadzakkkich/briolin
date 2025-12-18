from jose import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import HTTPException
import logging

from .config import settings


logger = logging.getLogger("briolin.jwt")


class JWTManager:
    """Менеджер JWT токенов для внутренней коммуникации"""
    
    @staticmethod
    def create_internal_token(user_data: Dict[str, Any]) -> str:
        """
        Создает внутренний JWT токен для передачи между сервисами
        """
        expires_minutes = settings.shared.jwt_expire_minutes
        payload = {
            "exp": datetime.utcnow() + timedelta(minutes=expires_minutes),
            "iat": datetime.utcnow(),
            "iss": settings.shared.jwt_issuer,
            "aud": settings.shared.jwt_audience,
            "user": user_data
        }
        
        token = jwt.encode(
            payload,
            settings.shared.jwt_secret,
            algorithm=settings.shared.jwt_algorithm
        )
        
        # Логирование создания токена
        expires_at = datetime.fromtimestamp(payload["exp"])
        logger.debug(
            f"Created JWT token for user '{user_data.get('username', 'unknown')}'. "
            f"Expires at: {expires_at.strftime('%H:%M:%S')} "
            f"(in {expires_minutes} minutes)"
        )
        
        return token
    
    @staticmethod
    def decode_internal_token(token: str, verify_exp: bool = True) -> Dict[str, Any]:
        """
        Декодирует и валидирует внутренний JWT токен
        """
        try:
            options = {}
            if not verify_exp:
                options = {"verify_exp": False}
            
            payload = jwt.decode(
                token,
                settings.shared.jwt_secret,
                algorithms=[settings.shared.jwt_algorithm],
                audience=settings.shared.jwt_audience,
                issuer=settings.shared.jwt_issuer,
                options=options
            )
            
            # Логирование успешной проверки
            if verify_exp:
                expires_at = datetime.fromtimestamp(payload["exp"])
                now = datetime.utcnow()
                time_left = (expires_at - now).total_seconds()
                user = payload.get("user", {})
                
                logger.debug(
                    f"JWT token validated for user '{user.get('username', 'unknown')}'. "
                    f"Expires in: {time_left:.0f} seconds"
                )
            
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            raise HTTPException(status_code=401, detail="Internal token expired")
        except jwt.JWTError as e:
            logger.warning(f"JWT token invalid: {e}")
            raise HTTPException(status_code=401, detail=f"Invalid internal token: {str(e)}")
    
    @staticmethod
    def is_token_valid(token: str) -> bool:
        """Проверяет валидность токена (включая expiration)"""
        try:
            JWTManager.decode_internal_token(token, verify_exp=True)
            return True
        except HTTPException:
            return False
    
    @staticmethod
    def get_token_info(token: str) -> Dict[str, Any]:
        """Получает информацию о токене без проверки expiration"""
        try:
            payload = JWTManager.decode_internal_token(token, verify_exp=False)
            expires_at = datetime.fromtimestamp(payload["exp"])
            created_at = datetime.fromtimestamp(payload["iat"])
            now = datetime.utcnow()
            user = payload.get("user", {})
            
            return {
                "valid": expires_at > now,
                "expired": expires_at <= now,
                "expires_at": expires_at,
                "created_at": created_at,
                "time_left_seconds": (expires_at - now).total_seconds(),
                "user": user.get("username"),
                "keycloak_id": user.get("keycloak_id")
            }
        except Exception as e:
            return {"error": str(e), "valid": False}


jwt_manager = JWTManager()