from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import KeycloakConnectionError

class KeycloakClient:
    def __init__(self):
        # Только для чтения информации из Keycloak
        # Обновление Keycloak теперь выполняется только через auth-service
        self._admin_connection = None

    @property
    def admin(self):
        """Ленивая инициализация админского подключения (только для чтения)"""
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
    
    def get_user_info(self, keycloak_id: str) -> Optional[Dict[str, Any]]:
        """Получение информации о пользователе из Keycloak (только чтение)"""
        try:
            user = self.admin.get_user(keycloak_id)
            return user
        except Exception as e:
            logger.error(f"Failed to get user info from Keycloak: {e}")
            return None
    
    def get_user_roles(self, keycloak_id: str) -> List[str]:
        """Получение ролей пользователя из Keycloak (только чтение)"""
        try:
            roles = self.admin.get_realm_roles_of_user(keycloak_id)
            # Фильтруем технические роли
            return [role['name'] for role in roles 
                   if role['name'] not in ['default-roles-briolin', 'offline_access']]
        except Exception as e:
            logger.error(f"Failed to get user roles from Keycloak: {e}")
            return []