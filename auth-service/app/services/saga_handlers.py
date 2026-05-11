import uuid
import json
import aio_pika
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.services.keycloak_client import KeycloakClient
from app.database.session import async_session_factory
from app.database.models import User
from app.core.config import settings
from app.core.logger import logger
from sqlalchemy import select, and_
from shared.saga.models import SagaOutbox, SagaStatus



class AuthSagaHandlers:
    """Обработчики шагов SAGA для auth-service"""
    
    def __init__(self):
        self.kc_client = KeycloakClient()
        self._email_channel = None
        self._email_connection = None
    
    async def _get_step_result(self, saga_id: str, step_name: str) -> Dict[str, Any]:
        """Вспомогательный метод для получения результата шага"""
        async with async_session_factory() as session:
            from shared.saga.models import SagaInstance
            stmt = select(SagaInstance).where(SagaInstance.saga_id == saga_id)
            result = await session.execute(stmt)
            instance = result.scalar_one_or_none()
            
            if instance and instance.step_results:
                return instance.step_results.get(step_name, {})
            return {}
    
    # ========== ОТПРАВКА EMAIL ==========
    
    async def _send_email_notification(self, email_type: str, to_email: str, **kwargs):
        """Отправить уведомление в email-сервис через RabbitMQ"""
        try:
            if not self._email_channel:
                connection = await aio_pika.connect_robust(
                    f"amqp://{settings.rabbitmq.user}:{settings.rabbitmq.password}@{settings.rabbitmq.host}:{settings.rabbitmq.port}/"
                )
                self._email_channel = await connection.channel()
                await self._email_channel.declare_queue("email.notifications", durable=True)
                self._email_connection = connection
            
            message = {
                "type": email_type,
                "to": to_email,
                **kwargs
            }
            
            await self._email_channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key="email.notifications"
            )
            logger.info(f"Email notification queued: {email_type} -> {to_email}")
            
        except Exception as e:
            logger.error(f"Failed to queue email notification: {e}")
    
    # ========== ОСНОВНЫЕ ШАГИ ==========
    
    # Удалены handle_create_keycloak_user и handle_create_auth_db_user,
    # так как регистрация теперь синхронная
    
    async def handle_update_keycloak_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Обновление пользователя в Keycloak"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        keycloak_id = payload.get("keycloak_id")
        update_data = payload.get("update_data", {})
        roles = payload.get("roles")
        
        logger.info(f"[SAGA {saga_id}] Updating user in Keycloak: {keycloak_id} with fields: {list(update_data.keys())}")
        
        try:
            # Обновляем основные данные
            if update_data:
                self.kc_client.update_user_in_keycloak(keycloak_id, update_data)
            
            # Обновляем роли, если они есть
            if roles is not None:
                self.kc_client.update_user_roles_in_keycloak(keycloak_id, roles)
            
            return {
                "status": "success",
                "keycloak_id": keycloak_id,
                "updated_fields": list(update_data.keys()) if update_data else [],
                "roles_updated": roles is not None,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"[SAGA {saga_id}] Failed to update user in Keycloak: {e}")
            raise
    
    async def handle_update_auth_db_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Обновление пользователя в auth-db"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        keycloak_id = payload.get("keycloak_id")
        update_data = payload.get("update_data", {})
        
        logger.info(f"[SAGA {saga_id}] Updating user in auth-db: {keycloak_id}")
        
        if not update_data:
            logger.warning(f"[SAGA {saga_id}] Empty update data for {keycloak_id}")
            return {"status": "success", "updated": False, "reason": "no_data"}
        
        async with async_session_factory() as session:
            stmt = select(User).where(User.keycloak_id == keycloak_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                error_msg = f"User {keycloak_id} not found in auth-db"
                logger.error(f"[SAGA {saga_id}] {error_msg}")
                raise Exception(error_msg)
            
            updated_fields = []
            if 'email' in update_data:
                user.email = update_data['email']
                updated_fields.append('email')
            if 'is_active' in update_data:
                user.is_active = update_data['is_active']
                updated_fields.append('is_active')
            
            await session.commit()
            
            logger.info(f"[SAGA {saga_id}] User updated in auth-db: {updated_fields}")
            
            return {
                "status": "success",
                "user_id": user.id,
                "keycloak_id": keycloak_id,
                "updated_fields": updated_fields
            }
    
    async def handle_delete_keycloak_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Удаление пользователя из Keycloak"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        keycloak_id = payload.get("keycloak_id")
        
        logger.info(f"[SAGA {saga_id}] Deleting user from Keycloak: {keycloak_id}")
        
        try:
            success = self.kc_client.delete_user_from_keycloak(keycloak_id)
            return {
                "status": "success" if success else "failed",
                "keycloak_id": keycloak_id,
                "deleted": success
            }
        except Exception as e:
            logger.error(f"[SAGA {saga_id}] Failed to delete user from Keycloak: {e}")
            raise
    
    async def handle_delete_auth_db_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Удаление пользователя из auth-db"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        keycloak_id = payload.get("keycloak_id")
        
        logger.info(f"[SAGA {saga_id}] Deleting user from auth-db: {keycloak_id}")
        
        async with async_session_factory() as session:
            stmt = select(User).where(User.keycloak_id == keycloak_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"[SAGA {saga_id}] User not found in auth-db")
                return {"status": "success", "deleted": False, "reason": "not_found"}
            
            await session.delete(user)
            await session.commit()
            
            logger.info(f"[SAGA {saga_id}] User deleted from auth-db")
            
            return {
                "status": "success",
                "user_id": user.id,
                "keycloak_id": keycloak_id,
                "deleted": True
            }
    
    # ========== ШАГИ ПУБЛИКАЦИИ СОБЫТИЙ ==========
    
    # Удален handle_publish_user_registered
    
    async def handle_publish_user_profile_updated(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Публикация USER_PROFILE_UPDATED"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        logger.info(f"[SAGA {saga_id}] Publishing USER_PROFILE_UPDATED confirmation")
        
        keycloak_id = payload.get("keycloak_id")
        user_id = payload.get("user_id")
        updated_fields = payload.get("updated_fields", {})
        source_service = payload.get("source_service", "auth-service")
        
        if not keycloak_id or not user_id:
            error_msg = f"[SAGA {saga_id}] Missing keycloak_id or user_id for event publication"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        from app.services.event_service import get_event_service
        event_service = get_event_service()
        
        success = await event_service.publish_user_profile_updated(
            keycloak_id=keycloak_id,
            user_id=user_id,
            updated_fields=updated_fields,
            correlation_id=saga_id,
            source_service=source_service
        )
        
        if not success:
            error_msg = f"[SAGA {saga_id}] Failed to publish USER_PROFILE_UPDATED event"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        logger.info(f"[SAGA {saga_id}] USER_PROFILE_UPDATED event published")
        return {"status": "success", "event_published": True}
    
    async def handle_publish_user_status_changed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Публикация USER_STATUS_CHANGED"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        logger.info(f"[SAGA {saga_id}] Publishing USER_STATUS_CHANGED event")
        
        keycloak_id = payload.get("keycloak_id")
        user_id = payload.get("user_id")
        is_active = payload.get("is_active")
        reason = payload.get("reason")
        source_service = payload.get("source_service", "auth-service")
        
        if not keycloak_id or not user_id or is_active is None:
            error_msg = f"[SAGA {saga_id}] Missing required fields for event publication"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        from app.services.event_service import get_event_service
        event_service = get_event_service()
        
        success = await event_service.publish_user_status_changed(
            keycloak_id=keycloak_id,
            user_id=user_id,
            is_active=is_active,
            reason=reason,
            correlation_id=saga_id,
            source_service=source_service
        )
        
        if not success:
            error_msg = f"[SAGA {saga_id}] Failed to publish USER_STATUS_CHANGED event"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        logger.info(f"[SAGA {saga_id}] USER_STATUS_CHANGED event published")
        return {"status": "success", "event_published": True}
    
    async def handle_publish_user_roles_updated(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Публикация USER_ROLES_UPDATED"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        logger.info(f"[SAGA {saga_id}] Publishing USER_ROLES_UPDATED confirmation")
        
        keycloak_id = payload.get("keycloak_id")
        user_id = payload.get("user_id")
        roles = payload.get("roles", [])
        old_roles = payload.get("old_roles", [])
        source_service = payload.get("source_service", "auth-service")
        
        if not keycloak_id or not user_id:
            error_msg = f"[SAGA {saga_id}] Missing keycloak_id or user_id for event publication"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        from app.services.event_service import get_event_service
        event_service = get_event_service()
        
        success = await event_service.publish_user_roles_updated(
            keycloak_id=keycloak_id,
            user_id=user_id,
            roles=roles,
            old_roles=old_roles,
            correlation_id=saga_id,
            source_service=source_service
        )
        
        if not success:
            error_msg = f"[SAGA {saga_id}] Failed to publish USER_ROLES_UPDATED event"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        logger.info(f"[SAGA {saga_id}] USER_ROLES_UPDATED event published")
        return {"status": "success", "event_published": True}
    
    async def handle_publish_user_deleted(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Публикация USER_DELETED"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        logger.info(f"[SAGA {saga_id}] Publishing USER_DELETED event")
        
        keycloak_id = payload.get("keycloak_id")
        user_id = payload.get("user_id")
        source_service = payload.get("source_service", "auth-service")
        
        if not keycloak_id:
            error_msg = f"[SAGA {saga_id}] Missing keycloak_id for event publication"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        from app.services.event_service import get_event_service
        event_service = get_event_service()
        
        success = await event_service.publish_user_deleted(
            keycloak_id=keycloak_id,
            user_id=user_id,
            correlation_id=saga_id,
            source_service=source_service
        )
        
        if not success:
            error_msg = f"[SAGA {saga_id}] Failed to publish USER_DELETED event"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        logger.info(f"[SAGA {saga_id}] USER_DELETED event published")
        return {"status": "success", "event_published": True}
    
    # ========== КОМПЕНСАЦИИ ==========
    
    # Удалены handle_compensate_create_keycloak_user и handle_compensate_create_auth_db_user
    
    async def handle_compensate_update_keycloak_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Компенсация: восстановление данных в Keycloak"""
        # Реализация при необходимости
        return {"status": "success"}
    
    async def handle_compensate_update_auth_db_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Компенсация: восстановление данных в auth-db"""
        # Реализация при необходимости
        return {"status": "success"}