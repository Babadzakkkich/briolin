from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List, Callable

from app.database.models import User, UserRole
from app.schemas.auth import UserRegister, UserLogin
from app.services.keycloak_client import KeycloakClient
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

    async def register(self, user_data: dict) -> Dict[str, Any]:
        """Регистрация пользователя"""
        # Преобразуем dict в UserRegister
        user_register = UserRegister(**user_data)
        
        # Проверка существования пользователя в локальной БД
        stmt = select(User).where(
            (User.email == user_register.email) | (User.username == user_register.username)
        )
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            logger.info(f"Registration failed: User {user_register.username} already exists locally")
            raise UserAlreadyExistsException()

        keycloak_id = None
        compensation_actions: List[Callable[[], None]] = []
        
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

        # Создание пользователя в локальной БД
        new_user = User(
            keycloak_id=keycloak_id,
            email=user_register.email,
            username=user_register.username,
            first_name=user_register.first_name,
            last_name=user_register.last_name
        )
        
        # Добавляем роль
        from app.database.models import UserRoleAssignment
        role_assignment = UserRoleAssignment(
            user=new_user,
            role=user_register.role
        )
        
        try:
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            
            compensation_actions.clear()
            
            logger.info(f"User registered successfully: {new_user.id} with role {user_register.role.value}")
            
            # Возвращаем информацию о пользователе
            return {
                "id": new_user.id,
                "keycloak_id": new_user.keycloak_id,
                "username": new_user.username,
                "email": new_user.email,
                "first_name": new_user.first_name,
                "last_name": new_user.last_name,
                "roles": [user_register.role.value],
                "is_active": new_user.is_active
            }
            
        except Exception as e:
            logger.error(f"DB Error during registration: {e}")
            await self.db.rollback()
            self.kc._execute_compensation(kc_compensation)
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
        except InvalidTokenException as e:
            # Пробрасываем InvalidTokenException с правильным сообщением
            raise e
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
        """Валидация токена (для совместимости)"""
        try:
            payload = self.kc.decode_token(token, validate=True)
            return {"valid": True, "payload": payload}
        except Exception as e:
            return {"valid": False, "error": str(e)}