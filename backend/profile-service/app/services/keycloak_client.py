from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError
from typing import Optional, Dict, Any

from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import KeycloakConnectionError

class KeycloakClient:
    """Клиент только для чтения данных из Keycloak"""
    def __init__(self):
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

    def get_user_info(self, keycloak_id: str) -> Optional[Dict[str, Any]]:
        """Получение информации о пользователе из Keycloak (только чтение)"""
        try:
            user = self.admin.get_user(keycloak_id)
            return user
        except Exception as e:
            logger.error(f"Failed to get user info from Keycloak: {e}")
            return None