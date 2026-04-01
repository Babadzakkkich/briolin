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
    Универсальный HTTP клиент для проксирования запросов к микросервисам
    """
    
    def __init__(self):
        self.timeout = httpx.Timeout(30.0)
        self.auth_service_url = settings.services.auth
        self.user_service_url = settings.services.user
        self.profile_service_url = settings.services.profile
        self.testing_service_url = settings.services.testing
        self.search_service_url = settings.services.search
        self.chat_service_url = settings.services.chat
        self.media_service_url = settings.services.media
    
    def _get_service_url(self, path: str) -> str:
        """Определяет URL сервиса по пути"""
        if path.startswith("/ws"):
            raise ValueError("WebSocket requests should not use HTTP client")
        
        if path.startswith("/api/v1/auth"):
            return self.auth_service_url
        elif path.startswith("/api/v1/users"):
            return self.user_service_url
        elif path.startswith("/api/v1/profiles"):
            return self.profile_service_url
        elif path.startswith("/api/v1/tests"):
            return self.testing_service_url
        elif path.startswith("/api/v1/search"):
            return self.search_service_url
        elif path.startswith("/api/v1/chats"):
            return self.chat_service_url
        elif path.startswith("/api/v1/internal/users"):
            return self.user_service_url
        elif path.startswith("/api/v1/internal/profiles"):
            return self.profile_service_url
        elif path.startswith("/api/v1/internal/tests"):
            return self.testing_service_url
        elif path.startswith("/api/v1/media"):
            return self.media_service_url
        else:
            return self.auth_service_url
    
    async def proxy_request(
        self,
        request: Request,
        path_override: Optional[str] = None
    ) -> httpx.Response:
        """Проксирование запроса к микросервису с внутренним токеном"""
        
        path = path_override if path_override else request.url.path
        
        # Проверяем, что это не WebSocket
        if path.startswith("/ws"):
            raise ValueError("Cannot proxy WebSocket through HTTP client. Use WebSocket proxy instead.")
        
        service_url = self._get_service_url(path)
        
        # Формируем URL для целевого сервиса
        target_url = urljoin(service_url.rstrip("/") + "/", path.lstrip("/"))
        
        # Формируем заголовки
        headers = {}
        
        # Копируем оригинальные заголовки (кроме host и content-length)
        for header_name, header_value in request.headers.items():
            header_name_lower = header_name.lower()
            if header_name_lower not in ['host', 'content-length', 'content-type']:
                headers[header_name] = header_value
        
        # Передаем внутренний токен если есть
        internal_token = request.headers.get("x-internal-token")
        signature = request.headers.get("x-token-signature")
        
        if internal_token and signature:
            headers["x-internal-token"] = internal_token
            headers["x-token-signature"] = signature
            logger.debug(f"Proxying with internal token: {internal_token[:30]}...")
        
        # Определяем тип содержимого
        content_type = request.headers.get("content-type", "")
        
        # Для multipart/form-data используем form_data
        if "multipart/form-data" in content_type:
            # Не передаем content-type, httpx сам установит правильный с boundary
            if "content-type" in headers:
                del headers["content-type"]
            
            # Получаем form data из request
            form_data = await request.form()
            
            # Создаем multipart данные для отправки
            files = []
            data = {}
            
            for key, value in form_data.items():
                # Проверяем, является ли значение файлом по наличию атрибутов
                if hasattr(value, 'filename') and hasattr(value, 'read') and hasattr(value, 'content_type'):
                    # Это файл - читаем содержимое
                    file_content = await value.read()
                    files.append(
                        (key, (value.filename, file_content, value.content_type))
                    )
                    logger.debug(f"Added file: {key} -> {value.filename} ({len(file_content)} bytes)")
                else:
                    # Это обычное поле
                    data[key] = value
                    logger.debug(f"Added data field: {key} -> {value}")
            
            logger.info(f"Proxying multipart request {request.method} {path} -> {target_url}")
            logger.debug(f"Files count: {len(files)}, Data fields: {list(data.keys())}")
            
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(
                        method=request.method,
                        url=target_url,
                        headers=headers,
                        data=data,
                        files=files,
                        params=request.query_params
                    )
                    
                    logger.debug(f"Proxied to service: {response.status_code}")
                    return response
            except Exception as e:
                logger.error(f"Error proxying multipart request: {e}", exc_info=True)
                raise
        
        # Для обычных запросов
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                if body_bytes:
                    try:
                        body_json = json.loads(body_bytes.decode())
                        logger.debug(f"Request body: {body_json}")
                    except:
                        pass
                    body = body_bytes
            except RuntimeError as e:
                if "Stream consumed" in str(e):
                    logger.error("Stream already consumed, cannot proxy request")
                    raise ServiceUnavailableException("Stream already consumed")
                raise
        
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
                
                logger.debug(f"Proxied to service: {response.status_code}")
                return response
                
        except httpx.ConnectError:
            logger.error(f"Cannot connect to service at {service_url}")
            raise ServiceUnavailableException("service")
        except Exception as e:
            logger.error(f"Error proxying request: {e}")
            raise ServiceUnavailableException("service")

http_client = HTTPClient()