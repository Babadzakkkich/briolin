from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List, Callable, Optional

from app.database.models import User
from app.schemas.auth import UserRegister, UserLogin
from app.services.keycloak_client import KeycloakClient
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
    def __init__(self, db: AsyncSession, kc_client: KeycloakClient):
        self.db = db
        self.kc = kc_client
        self.event_service = get_event_service()

    async def register(self, user_data: dict) -> Dict[str, Any]:
        """Регистрация пользователя с отправкой события"""
        user_register = UserRegister(**user_data)
        
        # Проверка существования пользователя в локальной БД
        stmt = select(User).where(User.email == user_register.email)
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            logger.info(f"Registration failed: User {user_register.email} already exists locally")
            raise UserAlreadyExistsException()

        keycloak_id = None
        compensation_actions: List[Callable[[], None]] = []
        user_created_in_db = False
        
        try:
            # Создание в Keycloak
            keycloak_id, kc_compensation = self.kc.create_user_with_compensation(
                email=user_register.email,
                username=user_register.username,
                password=user_register.password,
                first_name=user_register.first_name,
                last_name=user_register.last_name,
                role=user_register.role
            )
            compensation_actions.extend(kc_compensation)
            
        except Exception as e:
            if isinstance(e, UserAlreadyExistsException):
                raise e
            logger.error(f"Keycloak registration failed: {e}")
            raise KeycloakConnectionError(f"Registration failed in Identity Provider: {str(e)}")

        # Создание пользователя в локальной БД auth
        new_user = User(
            keycloak_id=keycloak_id,
            email=user_register.email,
        )
        
        try:
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            user_created_in_db = True
            
            logger.info(f"User registered in auth-db: {new_user.id}")
            
            # Отправляем событие о регистрации пользователя
            try:
                await self.event_service.publish_user_registered(
                    keycloak_id=keycloak_id,
                    email=user_register.email,
                    username=user_register.username,
                    first_name=user_register.first_name,
                    last_name=user_register.last_name,
                    role=user_register.role.value
                )
                logger.info(f"User registration event published for {keycloak_id}")
                
            except Exception as e:
                logger.error(f"Failed to publish user registration event: {e}")
                # Компенсация: удаляем пользователя из auth-db
                try:
                    await self.db.delete(new_user)
                    await self.db.commit()
                    user_created_in_db = False
                except Exception as db_error:
                    logger.error(f"Failed to delete user from auth-db during compensation: {db_error}")
                    await self.db.rollback()
                
                # Компенсация: удаляем пользователя из Keycloak
                self.kc._execute_compensation(compensation_actions)
                raise DatabaseException("Failed to publish user registration event")
            
            return {
                "id": new_user.id,
                "keycloak_id": new_user.keycloak_id,
                "email": new_user.email,
                "is_active": new_user.is_active
            }
            
        except Exception as e:
            logger.error(f"DB Error during registration: {e}")
            
            # Если пользователь был создан в БД, пытаемся удалить
            if user_created_in_db:
                try:
                    await self.db.rollback()
                    self.db.add(new_user)
                    await self.db.delete(new_user)
                    await self.db.commit()
                except Exception as delete_error:
                    logger.error(f"Failed to delete user during cleanup: {delete_error}")
                    await self.db.rollback()
            
            # Компенсация для Keycloak
            if compensation_actions:
                self.kc._execute_compensation(compensation_actions)
            
            if isinstance(e, DatabaseException):
                raise e
            else:
                raise DatabaseException("System error during registration")

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
        
    async def update_user_in_auth_db(
        self, 
        keycloak_id: str, 
        update_data: dict,
        source_service: str = "user-service"
    ) -> bool:
        """Обновление пользователя в auth-db с проверкой циклических событий"""
        stmt = select(User).where(User.keycloak_id == keycloak_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"User with keycloak_id {keycloak_id} not found in auth-db")
            return False
        
        try:
            # Обновляем только разрешенные поля
            old_values = {}
            if 'email' in update_data:
                old_values['email'] = user.email
                user.email = update_data['email']
            if 'is_active' in update_data:
                old_values['is_active'] = user.is_active
                user.is_active = update_data['is_active']
            
            await self.db.commit()
            logger.info(f"User {keycloak_id} updated in auth-db from {source_service}: {list(update_data.keys())}")
            
            # Публикуем событие об обновлении, добавляя текущий сервис в processed_by
            await self.event_service.publish_user_updated(
                keycloak_id=keycloak_id,
                updated_fields=update_data,
                old_values=old_values,
                processed_by=["auth-service"]  # Указываем, что auth-service уже обработал
            )
            logger.info(f"User update event published for {keycloak_id}")
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update user in auth-db: {e}")
            raise DatabaseException("Failed to update user in auth-db")

    async def delete_user_from_auth_db(self, keycloak_id: str) -> bool:
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
            logger.info(f"User {keycloak_id} deleted from auth-db")
            
            # Публикуем событие удаления, указывая что auth-service уже обработал
            await self.event_service.publish_user_deleted(
                keycloak_id=keycloak_id,
                processed_by=["auth-service"]
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