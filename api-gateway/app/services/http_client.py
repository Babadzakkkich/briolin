import httpx
from typing import Dict, Any, Optional
from fastapi import Request
from urllib.parse import urljoin
import json

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableException
from app.core.logger import logger


class HTTPClient:
    """
    Обновленный HTTP клиент для проксирования запросов
    Теперь передает внутренние JWT токены
    """
    
    def __init__(self):
        self.timeout = httpx.Timeout(30.0)
        self.auth_service_url = settings.services.auth
    
    async def proxy_request(
        self,
        request: Request,
        path_override: Optional[str] = None
    ) -> httpx.Response:
        """Проксирование запроса к auth-service с внутренним токеном"""
        
        # Определяем путь
        path = path_override if path_override else request.url.path
        
        # Формируем URL для auth-service
        target_url = urljoin(self.auth_service_url.rstrip("/") + "/", path.lstrip("/"))
        
        # Формируем заголовки
        headers = {}
        
        # Копируем оригинальные заголовки (кроме Authorization и host)
        for header_name, header_value in request.headers.items():
            header_name_lower = header_name.lower()
            if header_name_lower not in ['host', 'content-length', 'authorization']:
                headers[header_name] = header_value
        
        # Передаем внутренний токен если есть
        internal_token = request.headers.get("x-internal-token")
        signature = request.headers.get("x-token-signature")
        
        if internal_token and signature:
            headers["x-internal-token"] = internal_token
            headers["x-token-signature"] = signature
            logger.debug(f"Proxying with internal token: {internal_token[:30]}...")
        else:
            logger.warning("No internal token found for proxying")
        
        # Получаем тело запроса
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body_bytes = await request.body()
            if body_bytes:
                try:
                    # Пробуем преобразовать в JSON для логгирования
                    body_json = json.loads(body_bytes.decode())
                    logger.debug(f"Request body: {body_json}")
                    body = body_bytes
                except:
                    body = body_bytes
        
        logger.info(f"Proxying {request.method} {path} -> {target_url}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    content=body,
                    params=request.query_params
                )
                
                logger.debug(f"Proxied to auth-service: {response.status_code}")
                return response
                
        except httpx.ConnectError:
            logger.error(f"Cannot connect to auth-service at {self.auth_service_url}")
            raise ServiceUnavailableException("auth-service")
        except Exception as e:
            logger.error(f"Error proxying request: {e}")
            raise ServiceUnavailableException("auth-service")


http_client = HTTPClient()