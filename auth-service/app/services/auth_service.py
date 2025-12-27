import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List, Callable, Optional

from app.database.models import User
from app.schemas.auth import UserRegister, UserLogin
from app.services.keycloak_client import KeycloakClient
from app.services.event_service import get_event_service
from app.services.saga_service import get_auth_saga_service
from app.core.exceptions import (
    InvalidTokenException,
    UserAlreadyExistsException, 
    KeycloakConnectionError, 
    InvalidCredentialsException,
    ValidationException,
    DatabaseException
)
from app.core.logger import logger


class AuthService:
    def __init__(self, db: AsyncSession, kc_client: KeycloakClient):
        self.db = db
        self.kc = kc_client
        self.event_service = get_event_service()
        self.saga_service = get_auth_saga_service()

    async def register(self, user_data: dict) -> Dict[str, Any]:
        """Регистрация пользователя через SAGA транзакцию"""
        user_register = UserRegister(**user_data)
        
        # Запускаем SAGA транзакцию
        saga_result = await self.saga_service.execute_user_registration_saga(
            email=user_register.email,
            username=user_register.username,
            password=user_register.password,
            first_name=user_register.first_name,
            last_name=user_register.last_name,
            role=user_register.role.value  # Получаем строковое значение из enum
        )
        
        saga_id = saga_result["saga_id"]
        
        # Ждем завершения SAGA
        final_status = None
        for _ in range(30):  # Ждем до 30 секунд
            await asyncio.sleep(1)
            status = await self.saga_service.saga_orchestrator.get_saga_status(saga_id)
            
            if status["status"] in ["completed", "compensated", "failed"]:
                final_status = status
                break
        
        if not final_status:
            # Если SAGA не завершилась за 30 секунд
            raise DatabaseException("User registration timeout")
        
        if final_status["status"] == "completed":
            # Получаем keycloak_id из результатов SAGA
            keycloak_id = final_status["results"]["create_keycloak_user"]["result"]["keycloak_id"]
            
            # Находим пользователя в БД
            stmt = select(User).where(User.keycloak_id == keycloak_id)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                raise DatabaseException("User created in SAGA but not found in database")
            
            # Отправляем событие о регистрации пользователя
            try:
                await self.event_service.publish_user_registered(
                    keycloak_id=keycloak_id,
                    email=user_register.email,
                    username=user_register.username,
                    first_name=user_register.first_name,
                    last_name=user_register.last_name,
                    role=user_register.role.value  # Получаем строковое значение из enum
                )
                logger.info(f"User registration event published for {keycloak_id}")
                
            except Exception as e:
                logger.error(f"Failed to publish user registration event: {e}")
                # В реальной системе можно использовать outbox pattern
            
            return {
                "id": user.id,
                "keycloak_id": user.keycloak_id,
                "email": user.email,
                "is_active": user.is_active,
                "saga_id": saga_id
            }
        elif final_status["status"] == "compensated":
            error_msg = final_status.get("error", "Unknown error")
            raise DatabaseException(f"User registration failed: {error_msg}")
        else:
            error_msg = final_status.get("error", "Unknown error")
            raise DatabaseException(f"User registration failed: {error_msg}")

    async def update_user_in_auth_db(
        self, 
        keycloak_id: str, 
        update_data: dict,
        source_service: str = "user-service",
        correlation_id: str = None
    ) -> bool:
        """Обновление пользователя в auth-db через SAGA транзакцию"""
        stmt = select(User).where(User.keycloak_id == keycloak_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"User with keycloak_id {keycloak_id} not found in auth-db")
            return False
        
        # Сохраняем старые значения для компенсации
        old_values = {}
        if 'email' in update_data:
            old_values['email'] = user.email
        if 'is_active' in update_data:
            old_values['is_active'] = user.is_active
        
        # Запускаем SAGA транзакцию
        saga_result = await self.saga_service.execute_user_profile_update_saga(
            keycloak_id=keycloak_id,
            update_data=update_data,
            old_values=old_values
        )
        
        saga_id = saga_result["saga_id"]
        
        # Ждем завершения SAGA
        for _ in range(30):
            await asyncio.sleep(1)
            status = await self.saga_service.saga_orchestrator.get_saga_status(saga_id)
            
            if status["status"] in ["completed", "compensated", "failed"]:
                break
        
        final_status = await self.saga_service.saga_orchestrator.get_saga_status(saga_id)
        
        if final_status["status"] == "completed":
            logger.info(f"User {keycloak_id} updated successfully via SAGA")
            
            # Публикуем событие обновления
            await self.event_service.publish_user_profile_updated(
                keycloak_id=keycloak_id,
                user_id=user.id,
                updated_fields=update_data,
                old_values=old_values,
                correlation_id=correlation_id,
                source_service=source_service
            )
            
            return True
        else:
            logger.error(f"User update SAGA failed: {final_status.get('error')}")
            return False

    async def login(self, credentials: dict) -> Dict[str, Any]:
        """Аутентификация пользователя"""
        user_login = UserLogin(**credentials)
        try:
            return self.kc.get_token(user_login.username, user_login.password)
        except InvalidCredentialsException:
            logger.warning(f"Failed login attempt for username: {user_login.username}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}")
            raise KeycloakConnectionError("Authentication service temporarily unavailable")
    
    async def refresh_token(self, refresh_data: dict) -> Dict[str, Any]:
        """Обновление токена"""
        refresh_token = refresh_data.get("refresh_token")
        if not refresh_token:
            raise ValidationException("Refresh token required")
        
        try:
            return self.kc.refresh_token(refresh_token)
        except KeycloakConnectionError:
            raise KeycloakConnectionError("Auth service temporarily unavailable")
    
    async def logout(self, refresh_token: str) -> Dict[str, Any]:
        """Выход из системы"""
        try:
            self.kc.logout(refresh_token)
            return {"message": "Successfully logged out"}
        except InvalidTokenException:
            raise InvalidTokenException("Invalid refresh token")
        except KeycloakConnectionError:
            raise KeycloakConnectionError("Auth service temporarily unavailable")
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Валидация токена"""
        try:
            payload = self.kc.decode_token(token, validate=True)
            return {"valid": True, "payload": payload}
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    async def check_user_exists(self, keycloak_id: str) -> bool:
        """Проверка существования пользователя в auth-db"""
        stmt = select(User).where(User.keycloak_id == keycloak_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    async def check_user_active(self, keycloak_id: str) -> bool:
        """Проверка активности пользователя в auth-db"""
        stmt = select(User).where(User.keycloak_id == keycloak_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        return user.is_active if user else False
    
    async def get_user_basic_info(self, keycloak_id: str) -> Dict[str, Any]:
        """Получение базовой информации о пользователе из auth-db"""
        stmt = select(User).where(User.keycloak_id == keycloak_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        return {
            "id": user.id,
            "keycloak_id": user.keycloak_id,
            "email": user.email,
            "is_active": user.is_active,
            "created_at": user.created_at
        }

    async def delete_user_from_auth_db(
        self, 
        keycloak_id: str,
        correlation_id: str = None,
        source_service: str = "user-service"
    ) -> bool:
        """Удаление пользователя из auth-db (только для внутреннего использования)"""
        try:
            stmt = select(User).where(User.keycloak_id == keycloak_id)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"User {keycloak_id} not found in auth-db")
                return False
            
            await self.db.delete(user)
            await self.db.commit()
            logger.info(f"User {keycloak_id} deleted from auth-db (requested by {source_service})")
            
            # Публикуем событие удаления, указывая что auth-service уже обработал
            await self.event_service.publish_user_deleted(
                keycloak_id=keycloak_id,
                user_id=user.id,
                correlation_id=correlation_id,
                source_service=source_service
            )
            logger.info(f"User deletion event published for {keycloak_id}")
            
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete user from auth-db: {e}")
            return False

    async def update_user_email_in_keycloak(self, keycloak_id: str, email: str) -> bool:
        """Обновление email пользователя в Keycloak"""
        try:
            self.kc.update_user_in_keycloak(keycloak_id, {"email": email})
            logger.info(f"Email updated in Keycloak for user {keycloak_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update email in Keycloak for user {keycloak_id}: {e}")
            return False

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email"""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_keycloak_id(self, keycloak_id: str) -> Optional[User]:
        """Получение пользователя по keycloak_id"""
        stmt = select(User).where(User.keycloak_id == keycloak_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()