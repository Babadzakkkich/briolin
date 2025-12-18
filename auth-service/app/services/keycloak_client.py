from keycloak import KeycloakOpenID, KeycloakAdmin
from keycloak.exceptions import KeycloakError, KeycloakPostError, KeycloakAuthenticationError
from typing import List, Callable, Dict, Any, Tuple

from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import (
    KeycloakConnectionError, 
    InvalidCredentialsException,
    InvalidTokenException
)
from app.database.models import UserRole

class KeycloakClient:
    def __init__(self):
        # Клиент для Login (получение токена)
        self.oidc = KeycloakOpenID(
            server_url=settings.keycloak.server_url,
            client_id=settings.keycloak.client_id,
            realm_name=settings.keycloak.realm,
            client_secret_key=settings.keycloak.client_secret,
        )
        
        # Клиент для Admin API (создание юзеров)
        self._admin_connection = None

    @property
    def admin(self):
        """Ленивая инициализация админского подключения"""
        if not self._admin_connection:
            try:
                self._admin_connection = KeycloakAdmin(
                    server_url=settings.keycloak.server_url,
                    realm_name=settings.keycloak.realm,
                    username="admin",
                    password="admin",
                    verify=True,
                )
            except Exception as e:
                logger.error(f"Failed to connect to Keycloak Admin: {e}")
                raise KeycloakConnectionError("Keycloak Admin connection failed")
        return self._admin_connection

    def create_user_with_compensation(
        self, 
        email: str, 
        username: str, 
        password: str, 
        first_name: str, 
        last_name: str,
        role: UserRole = UserRole.USER
    ) -> Tuple[str, List[Callable[[], None]]]:
        """
        Создает пользователя в Keycloak и возвращает tuple:
        (user_id, список компенсирующих действий)
        """
        compensation_actions: List[Callable[[], None]] = []
        
        try:
            # 1. Создание пользователя
            user_payload = {
                "email": email,
                "username": username,
                "firstName": first_name,
                "lastName": last_name,
                "enabled": True,
                "emailVerified": False,
                "credentials": [{"value": password, "type": "password", "temporary": False}]
            }
            
            self.admin.create_user(user_payload)
            
            # Компенсирующее действие для создания пользователя
            def compensate_create_user():
                try:
                    logger.warning(f"Compensating: deleting user {username} from Keycloak")
                    self.admin.delete_user(username)
                except Exception as e:
                    logger.error(f"Failed to compensate user deletion: {e}")
            
            compensation_actions.append(compensate_create_user)
            
            # 2. Получение ID пользователя
            user_id = self.admin.get_user_id(username)
            if not user_id:
                raise KeycloakError("User created but ID not found")
            
            # 3. НАЗНАЧЕНИЕ REALM ROLE
            try:
                realm_role = self.admin.get_realm_role(role.value)
            except:
                # Если роль не существует, создаем ее
                self.admin.create_realm_role({
                    'name': role.value,
                    'description': f'{role.value} role'
                })
                realm_role = self.admin.get_realm_role(role.value)
            
            # Назначаем realm role пользователю
            self.admin.assign_realm_roles(user_id=user_id, roles=[realm_role])
            
            # Компенсирующее действие для назначения роли
            def compensate_role_assignment():
                try:
                    logger.warning(f"Compensating: removing realm role {role.value} from user {user_id}")
                    self.admin.delete_realm_roles_of_user(
                        user_id=user_id,
                        roles=[realm_role]
                    )
                except Exception as e:
                    logger.error(f"Failed to compensate role removal: {e}")
            
            compensation_actions.append(compensate_role_assignment)
            
            logger.info(f"User created in Keycloak: {user_id} with role {role.value}")
            return user_id, compensation_actions
            
        except Exception as e:
            # Если произошла ошибка, выполняем компенсацию
            logger.error(f"Keycloak create_user failed: {e}")
            self._execute_compensation(compensation_actions)
            raise

    def _execute_compensation(self, compensation_actions: List[Callable[[], None]]) -> None:
        """Выполняет компенсирующие действия в обратном порядке"""
        for action in reversed(compensation_actions):
            try:
                action()
            except Exception as e:
                logger.error(f"Compensation action failed: {e}")

    def get_token(self, username: str, password: str) -> Dict[str, Any]:
        """Синхронный метод получения токена"""
        try:
            return self.oidc.token(username, password)
        
        except KeycloakAuthenticationError as e:
            if e.response_code == 401:
                error_message = str(e).lower()
                if "invalid_grant" in error_message and ("invalid user credentials" in error_message or "user not found" in error_message):
                    raise InvalidCredentialsException("Invalid username or password")
                else:
                    logger.error(f"Keycloak authentication error: {e}")
                    raise InvalidTokenException("Authentication failed")
            else:
                logger.error(f"Unexpected KeycloakAuthenticationError: {e}")
                raise KeycloakConnectionError(f"Failed to get token: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting token: {e}")
            raise KeycloakConnectionError(f"Failed to get token: {e}")

    def update_user_in_keycloak(self, keycloak_id: str, user_data: dict, roles: list = None) -> None:
        """Обновление пользователя в Keycloak"""
        try:
            # Обновляем основные данные пользователя
            if user_data:
                self.admin.update_user(keycloak_id, user_data)
                logger.info(f"User {keycloak_id} updated in Keycloak: {list(user_data.keys())}")
            
            # Обновляем роли, если переданы
            if roles:
                # Получаем текущие роли пользователя
                current_roles = self.admin.get_realm_roles_of_user(keycloak_id)
                
                # Находим роли для добавления и удаления
                current_role_names = [r['name'] for r in current_roles]
                
                # Добавляем новые роли
                for role in roles:
                    if role not in current_role_names:
                        realm_role = self.admin.get_realm_role(role)
                        if realm_role:
                            self.admin.assign_realm_roles(user_id=keycloak_id, roles=[realm_role])
                
                # Удаляем старые роли, которых нет в новых
                for current_role in current_roles:
                    if current_role['name'] not in roles and current_role['name'] not in ['default-roles-briolin', 'offline_access']:
                        self.admin.delete_realm_roles_of_user(
                            user_id=keycloak_id,
                            roles=[current_role]
                        )
                
                logger.info(f"User {keycloak_id} roles updated in Keycloak: {roles}")
                
        except Exception as e:
            logger.error(f"Failed to update user {keycloak_id} in Keycloak: {e}")
            raise KeycloakConnectionError(f"Failed to update user in Keycloak: {str(e)}")
        
    def delete_user(self, user_id: str) -> None:
        """Синхронное удаление пользователя"""
        try:
            self.admin.delete_user(user_id)
            logger.warning(f"User {user_id} deleted from Keycloak (Rollback)")
        except Exception as e:
            logger.critical(f"Failed to delete user {user_id} during rollback: {e}")
            raise

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Обновление токена"""
        try:
            return self.oidc.refresh_token(refresh_token)
        except KeycloakPostError as e:
            # Проверяем тип ошибки
            error_message = str(e).lower()
            if e.response_code == 400 and "invalid_grant" in error_message:
                if "token is not active" in error_message or "token not active" in error_message:
                    raise InvalidTokenException("Refresh token is not active (already used)")
                elif "expired" in error_message:
                    raise InvalidTokenException("Refresh token has expired")
                else:
                    raise InvalidTokenException("Invalid refresh token")
            elif e.response_code == 401:
                raise InvalidTokenException("Invalid refresh token")
            else:
                logger.error(f"Keycloak refresh token error: {e}")
                raise KeycloakConnectionError(f"Failed to refresh token: {e}")
        except Exception as e:
            logger.error(f"Unexpected error refreshing token: {e}")
            raise KeycloakConnectionError(f"Failed to refresh token: {e}")

    def logout(self, refresh_token: str) -> None:
        """Выход из системы"""
        try:
            self.oidc.logout(refresh_token)
        except KeycloakPostError as e:
            if e.response_code == 400 and "invalid_grant" in str(e).lower():
                raise InvalidTokenException("Invalid refresh token")
            else:
                logger.error(f"Keycloak logout error: {e}")
                raise KeycloakConnectionError(f"Logout failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during logout: {e}")
            raise KeycloakConnectionError(f"Logout failed: {e}")

    def userinfo(self, access_token: str) -> Dict[str, Any]:
        """Получение информации о пользователе"""
        try:
            return self.oidc.userinfo(access_token)
        except KeycloakError as e:
            logger.error(f"Keycloak userinfo error: {e}")
            raise InvalidTokenException("Invalid access token")

    def decode_token(self, token: str, **kwargs) -> Dict[str, Any]:
        """Декодирование токена"""
        try:
            return self.oidc.decode_token(token, **kwargs)
        except Exception as e:
            logger.error(f"Token decode error: {e}")
            raise InvalidTokenException(f"Invalid token: {str(e)}")
    
    def get_user_roles(self, keycloak_id: str) -> List[str]:
        """Получение realm roles пользователя из Keycloak"""
        try:
            roles = self.admin.get_realm_roles_of_user(keycloak_id)
            # Фильтруем технические роли
            return [role['name'] for role in roles 
                   if role['name'] not in ['default-roles-briolin', 'offline_access']]
        except Exception as e:
            logger.error(f"Failed to get user roles from Keycloak: {e}")
            return []