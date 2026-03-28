import uuid
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.database.models import User
from app.schemas.auth import UserRegister, UserLogin, UserResponse
from app.services.keycloak_client import KeycloakClient
from app.services.user_service_client import get_user_service_client
from app.services.event_service import get_event_service
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
    def __init__(
        self, 
        db: AsyncSession, 
        kc_client: KeycloakClient
    ):
        self.db = db
        self.kc = kc_client
        self.event_service = get_event_service()
        self.user_service_client = get_user_service_client()

    # ========== РЕГИСТРАЦИЯ (СИНХРОННАЯ) ==========
    
    async def register(self, user_data: dict) -> UserResponse:
        """СИНХРОННАЯ регистрация пользователя"""
        try:
            user_register = UserRegister(**user_data)
        except Exception as e:
            raise ValidationException(f"Invalid registration data: {str(e)}")
        
        # Проверки существования
        existing_by_email = self.kc.get_user_by_email(user_register.email)
        if existing_by_email:
            raise UserAlreadyExistsException(f"User with email {user_register.email} already exists")
        
        existing_by_username = self.kc.get_user_by_username(user_register.username)
        if existing_by_username:
            raise UserAlreadyExistsException(f"User with username {user_register.username} already exists")
        
        stmt = select(User).where(User.email == user_register.email)
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise UserAlreadyExistsException(f"User with email {user_register.email} already exists")
        
        # Шаг 1: Создание пользователя в Keycloak
        try:
            keycloak_id, compensation_actions = self.kc.create_user_with_compensation(
                email=user_register.email,
                username=user_register.username,
                password=user_register.password,
                role="user"
            )
        except Exception as e:
            logger.error(f"Failed to create user in Keycloak: {e}")
            raise KeycloakConnectionError(f"Failed to create user in Keycloak: {str(e)}")
        
        # Шаг 2: Создание пользователя в auth-db
        try:
            new_user = User(
                keycloak_id=keycloak_id,
                email=user_register.email,
                is_active=True
            )
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            
            logger.info(f"User created in auth-db: {new_user.id} ({keycloak_id})")
        except Exception as e:
            # Компенсация: удаляем из Keycloak
            logger.error(f"Failed to create user in auth-db: {e}")
            self.kc.delete_user_from_keycloak(keycloak_id)
            raise DatabaseException(f"Failed to create user in database: {str(e)}")
        
        # Шаг 3: Синхронное создание профиля в user-service
        try:
            profile_data = await self.user_service_client.create_user_profile(
                keycloak_id=keycloak_id,
                email=user_register.email,
                username=user_register.username,
                role="user"
            )
            
            if not profile_data:
                # Компенсация: удаляем из Keycloak и auth-db
                logger.error("Failed to create user profile in user-service")
                self.kc.delete_user_from_keycloak(keycloak_id)
                await self.db.delete(new_user)
                await self.db.commit()
                raise DatabaseException("Failed to create user profile")
            
            logger.info(f"User profile created in user-service: {keycloak_id}")
            
        except UserAlreadyExistsException:
            # Пользователь уже существует в user-service - это странно, но обрабатываем
            logger.warning(f"User already exists in user-service for {keycloak_id}")
            # Продолжаем, так как пользователь уже есть
        except Exception as e:
            # Компенсация: удаляем из Keycloak и auth-db
            logger.error(f"Failed to create user profile in user-service: {e}")
            self.kc.delete_user_from_keycloak(keycloak_id)
            await self.db.delete(new_user)
            await self.db.commit()
            raise DatabaseException(f"Failed to create user profile: {str(e)}")
        
        return UserResponse(
            id=new_user.id,
            keycloak_id=keycloak_id,
            email=new_user.email,
            is_active=new_user.is_active
        )
    
    # ========== ОБНОВЛЕНИЕ ПРОФИЛЯ (ОСТАЕТСЯ АСИНХРОННЫМ) ==========
    
    async def update_user_in_auth_db(
        self, 
        keycloak_id: str, 
        update_data: dict,
        source_service: str = "user-service",
        correlation_id: str = None
    ) -> bool:
        """Обновление пользователя в auth-db через SAGA"""
        if not update_data:
            logger.warning(f"Empty update data for {keycloak_id}")
            return True
        
        correlation_id = correlation_id or str(uuid.uuid4())
        
        # Находим пользователя
        stmt = select(User).where(User.keycloak_id == keycloak_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"User with keycloak_id {keycloak_id} not found in auth-db")
            return False
        
        # Сохраняем старое состояние для компенсации
        old_values = {}
        if 'email' in update_data:
            old_values['email'] = user.email
        if 'is_active' in update_data:
            old_values['is_active'] = user.is_active
        
        # Создаем шаги саги
        saga_id = str(uuid.uuid4())
        
        # Шаг 1: Обновление в Keycloak (если есть поля для Keycloak)
        keycloak_fields = {}
        if 'email' in update_data:
            keycloak_fields['email'] = update_data['email']
        if 'username' in update_data:
            keycloak_fields['username'] = update_data['username']
        if 'first_name' in update_data:
            keycloak_fields['firstName'] = update_data['first_name']
        if 'last_name' in update_data:
            keycloak_fields['lastName'] = update_data['last_name']
        
        if keycloak_fields:
            from app.services.saga_worker import get_saga_worker
            saga_worker = get_saga_worker()
            
            await saga_worker.create_saga_outbox(
                saga_id=saga_id,
                saga_name="user_profile_update",
                step_name="update_keycloak_user",
                event_type="saga.step.update_keycloak_user",
                payload={
                    "keycloak_id": keycloak_id,
                    "update_data": keycloak_fields,
                    "old_values": old_values
                },
                headers={
                    "source_service": source_service,
                    "correlation_id": correlation_id
                }
            )
        
        # Шаг 2: Обновление в auth-db
        auth_fields = {}
        if 'email' in update_data:
            auth_fields['email'] = update_data['email']
        if 'is_active' in update_data:
            auth_fields['is_active'] = update_data['is_active']
        
        if auth_fields:
            from app.services.saga_worker import get_saga_worker
            saga_worker = get_saga_worker()
            
            depends_on = ["update_keycloak_user"] if keycloak_fields else None
            
            await saga_worker.create_saga_outbox(
                saga_id=saga_id,
                saga_name="user_profile_update",
                step_name="update_auth_db_user",
                event_type="saga.step.update_auth_db_user",
                payload={
                    "keycloak_id": keycloak_id,
                    "update_data": auth_fields,
                    "user_id": user.id
                },
                headers={
                    "source_service": source_service,
                    "correlation_id": correlation_id,
                    "depends_on": depends_on
                }
            )
        
        # Шаг 3: Публикация USER_PROFILE_UPDATED (после обоих обновлений)
        depends_on = []
        if keycloak_fields:
            depends_on.append("update_keycloak_user")
        if auth_fields:
            depends_on.append("update_auth_db_user")
        
        from app.services.saga_worker import get_saga_worker
        saga_worker = get_saga_worker()
        
        await saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="user_profile_update",
            step_name="publish_user_profile_updated",
            event_type="saga.step.publish_user_profile_updated",
            payload={
                "keycloak_id": keycloak_id,
                "user_id": user.id,
                "updated_fields": {**keycloak_fields, **auth_fields},
                "old_values": old_values,
                "source_service": source_service
            },
            headers={
                "source_service": "auth-service",
                "correlation_id": correlation_id,
                "depends_on": depends_on if depends_on else None
            }
        )
        
        logger.info(f"User update initiated for {keycloak_id} with saga_id: {saga_id}")
        return True
    
    # ========== ИЗМЕНЕНИЕ СТАТУСА (ОСТАЕТСЯ АСИНХРОННЫМ) ==========
    
    async def change_user_status(
        self,
        keycloak_id: str,
        is_active: bool,
        user_id: int,
        reason: str = None,
        source_service: str = "user-service",
        correlation_id: str = None
    ) -> bool:
        """Изменение статуса пользователя через SAGA"""
        correlation_id = correlation_id or str(uuid.uuid4())
        saga_id = str(uuid.uuid4())
        
        from app.services.saga_worker import get_saga_worker
        saga_worker = get_saga_worker()
        
        # Шаг 1: Обновление в Keycloak
        await saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="user_status_update",
            step_name="update_keycloak_user",
            event_type="saga.step.update_keycloak_user",
            payload={
                "keycloak_id": keycloak_id,
                "update_data": {"enabled": is_active}
            },
            headers={
                "source_service": source_service,
                "correlation_id": correlation_id
            }
        )
        
        # Шаг 2: Обновление в auth-db
        await saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="user_status_update",
            step_name="update_auth_db_user",
            event_type="saga.step.update_auth_db_user",
            payload={
                "keycloak_id": keycloak_id,
                "update_data": {"is_active": is_active},
                "user_id": user_id
            },
            headers={
                "source_service": source_service,
                "correlation_id": correlation_id,
                "depends_on": "update_keycloak_user"
            }
        )
        
        # Шаг 3: Публикация USER_STATUS_CHANGED
        await saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="user_status_update",
            step_name="publish_user_status_changed",
            event_type="saga.step.publish_user_status_changed",
            payload={
                "keycloak_id": keycloak_id,
                "user_id": user_id,
                "is_active": is_active,
                "reason": reason,
                "source_service": source_service
            },
            headers={
                "source_service": "auth-service",
                "correlation_id": correlation_id,
                "depends_on": ["update_keycloak_user", "update_auth_db_user"]
            }
        )
        
        logger.info(f"Status change initiated for {keycloak_id} with saga_id: {saga_id}")
        return True
    
    # ========== ОБНОВЛЕНИЕ РОЛЕЙ (ОСТАЕТСЯ АСИНХРОННЫМ) ==========
    
    async def update_user_roles(
        self,
        keycloak_id: str,
        user_id: int,
        roles: list,
        old_roles: list = None,
        source_service: str = "user-service",
        correlation_id: str = None
    ) -> bool:
        """Обновление ролей пользователя через SAGA"""
        correlation_id = correlation_id or str(uuid.uuid4())
        saga_id = str(uuid.uuid4())
        
        from app.services.saga_worker import get_saga_worker
        saga_worker = get_saga_worker()
        
        # Шаг 1: Обновление ролей в Keycloak
        await saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="user_roles_update",
            step_name="update_keycloak_user",
            event_type="saga.step.update_keycloak_user",
            payload={
                "keycloak_id": keycloak_id,
                "update_data": {},
                "roles": roles
            },
            headers={
                "source_service": source_service,
                "correlation_id": correlation_id
            }
        )
        
        # Шаг 2: Публикация USER_ROLES_UPDATED
        await saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="user_roles_update",
            step_name="publish_user_roles_updated",
            event_type="saga.step.publish_user_roles_updated",
            payload={
                "keycloak_id": keycloak_id,
                "user_id": user_id,
                "roles": roles,
                "old_roles": old_roles or [],
                "source_service": source_service
            },
            headers={
                "source_service": "auth-service",
                "correlation_id": correlation_id,
                "depends_on": "update_keycloak_user"
            }
        )
        
        logger.info(f"Roles update initiated for {keycloak_id} with saga_id: {saga_id}")
        return True
    
    # ========== УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ (ОСТАЕТСЯ АСИНХРОННЫМ) ==========
    
    async def delete_user_from_auth_db(
        self, 
        keycloak_id: str,
        correlation_id: str = None,
        source_service: str = "user-service"
    ) -> bool:
        """Удаление пользователя из auth-db через SAGA"""
        correlation_id = correlation_id or str(uuid.uuid4())
        
        # Находим пользователя
        stmt = select(User).where(User.keycloak_id == keycloak_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"User {keycloak_id} not found in auth-db")
            return False
        
        saga_id = str(uuid.uuid4())
        
        from app.services.saga_worker import get_saga_worker
        saga_worker = get_saga_worker()
        
        # Шаг 1: Удаление из Keycloak
        await saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="user_deletion",
            step_name="delete_keycloak_user",
            event_type="saga.step.delete_keycloak_user",
            payload={
                "keycloak_id": keycloak_id
            },
            headers={
                "source_service": source_service,
                "correlation_id": correlation_id
            }
        )
        
        # Шаг 2: Удаление из auth-db
        await saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="user_deletion",
            step_name="delete_auth_db_user",
            event_type="saga.step.delete_auth_db_user",
            payload={
                "keycloak_id": keycloak_id,
                "user_id": user.id
            },
            headers={
                "source_service": source_service,
                "correlation_id": correlation_id,
                "depends_on": "delete_keycloak_user"
            }
        )
        
        # Шаг 3: Публикация USER_DELETED
        await saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="user_deletion",
            step_name="publish_user_deleted",
            event_type="saga.step.publish_user_deleted",
            payload={
                "keycloak_id": keycloak_id,
                "user_id": user.id,
                "source_service": source_service
            },
            headers={
                "source_service": "auth-service",
                "correlation_id": correlation_id,
                "depends_on": ["delete_keycloak_user", "delete_auth_db_user"]
            }
        )
        
        logger.info(f"Deletion initiated for {keycloak_id} with saga_id: {saga_id}")
        return True
    
    # ========== СИНХРОННЫЕ МЕТОДЫ (БЕЗ ИЗМЕНЕНИЙ) ==========
    
    async def login(self, credentials: dict) -> Dict[str, Any]:
        """Аутентификация пользователя"""
        try:
            user_login = UserLogin(**credentials)
        except Exception as e:
            raise ValidationException(f"Invalid login data: {str(e)}")
        
        try:
            token_response = self.kc.get_token(user_login.username, user_login.password)
            
            token_info = self.kc.decode_token(token_response["access_token"])
            keycloak_id = token_info.get("sub")
            
            if keycloak_id:
                user = await self.get_user_by_keycloak_id(keycloak_id)
                if not user:
                    logger.error(f"User {keycloak_id} exists in Keycloak but not in auth-db")
                    raise DatabaseException("User account incomplete. Please contact support.")
            
            return token_response
            
        except InvalidCredentialsException:
            logger.warning(f"Failed login attempt for username: {user_login.username}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}")
            raise KeycloakConnectionError("Authentication service temporarily unavailable")
    
    async def refresh_token(self, refresh_data: dict) -> Dict[str, Any]:
        refresh_token = refresh_data.get("refresh_token")
        if not refresh_token:
            raise ValidationException("Refresh token required")
        
        try:
            return self.kc.refresh_token(refresh_token)
        except InvalidTokenException:
            raise
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            raise KeycloakConnectionError("Auth service temporarily unavailable")
    
    async def logout(self, refresh_token: str) -> Dict[str, Any]:
        if not refresh_token:
            raise ValidationException("Refresh token required")
        
        try:
            self.kc.logout(refresh_token)
            return {"message": "Successfully logged out"}
        except InvalidTokenException:
            raise
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            raise KeycloakConnectionError("Auth service temporarily unavailable")
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = self.kc.decode_token(token, validate=True)
            return {"valid": True, "payload": payload}
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    async def check_user_exists(self, keycloak_id: str) -> bool:
        stmt = select(User).where(User.keycloak_id == keycloak_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    async def check_user_active(self, keycloak_id: str) -> bool:
        stmt = select(User).where(User.keycloak_id == keycloak_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        return user.is_active if user else False
    
    async def get_user_basic_info(self, keycloak_id: str) -> Optional[Dict[str, Any]]:
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
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    
    async def update_user_email_in_keycloak(self, keycloak_id: str, email: str) -> bool:
        try:
            self.kc.update_user_in_keycloak(keycloak_id, {"email": email})
            logger.info(f"Email updated in Keycloak for user {keycloak_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update email in Keycloak for user {keycloak_id}: {e}")
            return False
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_keycloak_id(self, keycloak_id: str) -> Optional[User]:
        stmt = select(User).where(User.keycloak_id == keycloak_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()