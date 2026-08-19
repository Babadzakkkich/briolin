import time
import urllib.request
import json
from typing import Dict, Any, Optional

from jose import jwt, JWTError, ExpiredSignatureError

from app.core.config import settings
from app.core.exceptions import AuthenticationException
from app.core.logger import logger


class KeycloakClient:
    """
    Проверка Keycloak access token без gateway client_id/client_secret.

    Gateway больше не делает token introspection, потому что introspection требует
    client_id/client_secret и может ломаться, если токен выдан другому клиенту.
    Вместо этого access token проверяется локально как JWT:
    - подпись RS256 по JWKS публичному ключу Keycloak realm;
    - срок действия exp;
    - issuer;
    - тип токена Bearer.

    Audience намеренно не проверяется, потому что в текущей конфигурации Keycloak
    токен приходит с aud="account", а не с отдельным audience для gateway.
    """

    def __init__(self):
        server_url = settings.keycloak.server_url.rstrip("/")
        realm = settings.keycloak.realm

        self.issuer = f"{server_url}/realms/{realm}"
        self.jwks_url = f"{self.issuer}/protocol/openid-connect/certs"
        self.algorithms = ["RS256"]
        self._jwks: Optional[Dict[str, Any]] = None
        self._jwks_loaded_at: float = 0
        self._jwks_ttl_seconds: int = 300

    def _load_jwks(self, force_refresh: bool = False) -> Dict[str, Any]:
        now = time.time()
        if (
            not force_refresh
            and self._jwks is not None
            and now - self._jwks_loaded_at < self._jwks_ttl_seconds
        ):
            return self._jwks

        try:
            with urllib.request.urlopen(self.jwks_url, timeout=10) as response:
                raw_data = response.read().decode("utf-8")
                self._jwks = json.loads(raw_data)
                self._jwks_loaded_at = now
                return self._jwks
        except Exception as e:
            logger.error(f"Failed to load Keycloak JWKS from {self.jwks_url}: {e}")
            raise AuthenticationException("Cannot load Keycloak public keys")

    def _get_signing_key(self, token: str) -> Dict[str, Any]:
        try:
            header = jwt.get_unverified_header(token)
        except JWTError as e:
            logger.debug(f"Cannot read JWT header: {e}")
            raise AuthenticationException("Invalid token")

        kid = header.get("kid")
        if not kid:
            raise AuthenticationException("Invalid token: missing kid")

        for force_refresh in (False, True):
            jwks = self._load_jwks(force_refresh=force_refresh)
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    return key

        logger.warning(f"JWT signing key with kid={kid} not found in Keycloak JWKS")
        raise AuthenticationException("Invalid token key")

    def validate_token(self, token: str) -> Dict[str, Any]:
        """Локальная проверка access token по JWKS без client_id/client_secret."""
        try:
            signing_key = self._get_signing_key(token)
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=self.algorithms,
                issuer=self.issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": False,
                    "verify_aud": False,
                    "verify_iss": True,
                },
            )

            if payload.get("typ") != "Bearer":
                raise AuthenticationException("Invalid token type")

            return payload

        except ExpiredSignatureError:
            raise AuthenticationException("Token has expired")
        except AuthenticationException:
            raise
        except JWTError as e:
            logger.warning(f"JWT validation failed: {e}")
            raise AuthenticationException("Invalid token")
        except Exception as e:
            logger.error(f"Token validation failed: {e}", exc_info=True)
            raise AuthenticationException("Invalid token")

    def introspect_token(self, token: str) -> Dict[str, Any]:
        """
        Обратная совместимость со старым кодом.

        Метод больше не вызывает Keycloak introspection endpoint, а возвращает
        payload локально проверенного JWT.
        """
        return self.validate_token(token)


keycloak_client = KeycloakClient()
