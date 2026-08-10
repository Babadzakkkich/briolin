from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakError
from typing import Dict, Any
import time
import json

from app.core.config import settings
from app.core.exceptions import AuthenticationException
from app.core.logger import logger

class KeycloakClient:
    def __init__(self):
        # Используем общую конфигурацию Keycloak
        server_url = settings.keycloak.server_url
        realm = settings.keycloak.realm
        
        # Используем специфичные для api-gateway настройки клиента
        client_id = settings.gateway_keycloak.client_id
        client_secret = settings.gateway_keycloak.client_secret
        
        self.oidc = KeycloakOpenID(
            server_url=server_url,
            client_id=client_id,
            realm_name=realm,
            client_secret_key=client_secret,
        )
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """Валидация токена через Keycloak"""
        try:
            # Декодируем и валидируем токен
            return self.oidc.decode_token(
                token,
                key=self.oidc.public_key,
                options={
                    "verify_signature": True,
                    "verify_aud": True,
                    "verify_exp": True
                }
            )
        except KeycloakError as e:
            error_message = str(e)
            if "expired" in error_message.lower():
                raise AuthenticationException("Token has expired")
            elif "invalid" in error_message.lower():
                raise AuthenticationException("Invalid token")
            else:
                logger.error(f"Token validation failed: {e}")
                raise AuthenticationException("Invalid or expired token")
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            raise AuthenticationException("Invalid or expired token")
    
    def get_user_info(self, token: str) -> Dict[str, Any]:
        """Получение информации о пользователе"""
        try:
            return self.oidc.userinfo(token)
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            raise AuthenticationException("Cannot get user information")
    
    def introspect_token(self, token: str) -> Dict[str, Any]:
        """Проверка токена через Keycloak Introspection"""
        try:
            result = self.oidc.introspect(token)
            
            # Проверяем активен ли токен
            if not result.get("active", False):
                # Проверяем причину неактивности
                if result.get("exp", 0) < time.time():
                    raise AuthenticationException("Token has expired")
                elif result.get("token_type") != "Bearer":
                    raise AuthenticationException("Invalid token type")
                else:
                    raise AuthenticationException("Token is not active")
                    
            return result
            
        except KeycloakError as e:
            error_message = str(e)
            if "expired" in error_message.lower():
                raise AuthenticationException("Token has expired")
            elif "invalid" in error_message.lower():
                raise AuthenticationException("Invalid token")
            else:
                logger.error(f"Token introspection failed: {e}")
                raise AuthenticationException("Token introspection failed")
        except AuthenticationException:
            raise  # Пропускаем наши кастомные исключения
        except Exception as e:
            logger.error(f"Token introspection failed: {e}")
            raise AuthenticationException("Token introspection failed")

keycloak_client = KeycloakClient()