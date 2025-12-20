from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import KeycloakConnectionError

class KeycloakClient:
    def __init__(self):
        # Клиент для Admin API (управление пользователями)
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
    
    def update_user_in_keycloak(self, keycloak_id: str, user_data: dict) -> None:
        """Обновление пользователя в Keycloak"""
        try:
            # Обновляем основные данные пользователя
            if user_data:
                # Преобразуем имена полей в формат Keycloak
                kc_data = {}
                if 'email' in user_data:
                    kc_data['email'] = user_data['email']
                if 'first_name' in user_data:
                    kc_data['firstName'] = user_data['first_name']
                if 'last_name' in user_data:
                    kc_data['lastName'] = user_data['last_name']
                if 'username' in user_data:
                    kc_data['username'] = user_data['username']
                
                self.admin.update_user(keycloak_id, kc_data)
                logger.info(f"User {keycloak_id} updated in Keycloak: {list(kc_data.keys())}")
                
        except Exception as e:
            logger.error(f"Failed to update user {keycloak_id} in Keycloak: {e}")
            raise KeycloakConnectionError(f"Failed to update user in Keycloak: {str(e)}")

    def update_user_status_in_keycloak(self, keycloak_id: str, enabled: bool) -> None:
        """Обновление статуса пользователя в Keycloak"""
        try:
            self.admin.update_user(keycloak_id, {"enabled": enabled})
            logger.info(f"User {keycloak_id} status updated in Keycloak: {enabled}")
        except Exception as e:
            logger.error(f"Failed to update user status {keycloak_id} in Keycloak: {e}")
            raise KeycloakConnectionError(f"Failed to update user status in Keycloak: {str(e)}")

    def delete_user_from_keycloak(self, keycloak_id: str) -> None:
        """Удаление пользователя из Keycloak"""
        try:
            self.admin.delete_user(keycloak_id)
            logger.warning(f"User {keycloak_id} deleted from Keycloak")
        except Exception as e:
            logger.critical(f"Failed to delete user {keycloak_id} from Keycloak: {e}")
            raise KeycloakConnectionError(f"Failed to delete user from Keycloak: {str(e)}")

    def update_user_roles_in_keycloak(self, keycloak_id: str, roles: List[str]) -> None:
        """Обновление ролей пользователя в Keycloak"""
        try:
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
            logger.error(f"Failed to update user roles {keycloak_id} in Keycloak: {e}")
            raise KeycloakConnectionError(f"Failed to update user roles in Keycloak: {str(e)}")