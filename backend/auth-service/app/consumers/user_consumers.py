import json
from typing import Dict, Any
from shared.events.schemas import EventType
from app.services.rabbitmq import rabbitmq_consumer
from app.services.auth_service import AuthService
from app.database.session import async_session_factory
from app.core.config import settings
from app.core.logger import logger
from app.services.keycloak_client import KeycloakClient
from app.services.saga_worker import get_saga_worker  # Импортируем saga_worker

async def handle_user_profile_update_requested(event: Dict[str, Any]) -> bool:
    """Обработка события запроса на обновление профиля пользователя из user-service"""
    try:
        # Преобразуем в BaseEvent для удобства
        from shared.events.schemas import BaseEvent
        base_event = BaseEvent(**event)
        
        # Проверяем, не обрабатывали ли мы уже это событие
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed by auth-service")
            return True
        
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        updated_fields = user_data.get("updated_fields", {})
        correlation_id = base_event.correlation_id
        source_service = base_event.source_service
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in user profile update request")
            return False
        
        logger.info(f"Processing profile update request for {keycloak_id} from {source_service}: {updated_fields}")
        
        async with async_session_factory() as session:
            from app.services.keycloak_client import KeycloakClient
            kc_client = KeycloakClient()
            saga_worker = get_saga_worker()
            auth_service = AuthService(session, kc_client, saga_worker)
            
            keycloak_update_fields = {}
            if 'email' in updated_fields:
                keycloak_update_fields['email'] = updated_fields['email']
            if 'username' in updated_fields:
                keycloak_update_fields['username'] = updated_fields['username']  # username поддерживается!
            if 'first_name' in updated_fields:
                keycloak_update_fields['firstName'] = updated_fields['first_name']  # firstName, не first_name
            if 'last_name' in updated_fields:
                keycloak_update_fields['lastName'] = updated_fields['last_name']    # lastName, не last_name
            
            # Обновляем в Keycloak (только auth-service имеет право!)
            if keycloak_update_fields:
                try:
                    logger.info(f"Updating Keycloak user {keycloak_id} with fields: {list(keycloak_update_fields.keys())}")
                    kc_client.update_user_in_keycloak(keycloak_id, keycloak_update_fields)
                    logger.info(f"User {keycloak_id} updated in Keycloak")
                except Exception as e:
                    logger.error(f"Failed to update user {keycloak_id} in Keycloak: {e}")
                    return False
            
            # Определяем поля для обновления в auth-db
            auth_update_fields = {}
            if 'email' in updated_fields:
                auth_update_fields['email'] = updated_fields['email']
            if 'is_active' in updated_fields:
                auth_update_fields['is_active'] = updated_fields['is_active']
            
            # Обновляем в auth-db
            if auth_update_fields:
                success = await auth_service.update_user_in_auth_db(
                    keycloak_id=keycloak_id,
                    update_data=auth_update_fields,
                    source_service=source_service,
                    correlation_id=correlation_id
                )
                
                if not success:
                    logger.warning(f"User {keycloak_id} not found in auth-db")
                    return False
            
            logger.info(f"Profile update for {keycloak_id} processed and confirmed")
            return True
            
    except Exception as e:
        logger.error(f"Error handling user profile update request: {e}", exc_info=True)
        return False

async def handle_user_status_change_requested(event: Dict[str, Any]) -> bool:
    """Обработка события запроса изменения статуса пользователя из user-service"""
    try:
        from shared.events.schemas import BaseEvent
        base_event = BaseEvent(**event)
        
        # Проверяем, не обрабатывали ли мы уже это событие
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed by auth-service")
            return True
        
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        is_active = user_data.get("is_active")
        correlation_id = base_event.correlation_id
        source_service = base_event.source_service
        
        if not keycloak_id or is_active is None:
            logger.error("Missing keycloak_id or is_active in user status change request")
            return False
        
        logger.info(f"Processing status change request for {keycloak_id} from {source_service}: {is_active}")
        
        async with async_session_factory() as session:
            from app.services.keycloak_client import KeycloakClient
            kc_client = KeycloakClient()
            saga_worker = get_saga_worker()  # Получаем saga_worker
            auth_service = AuthService(session, kc_client, saga_worker)  # Передаём все три аргумента
            
            # Обновляем статус в Keycloak
            try:
                kc_client.update_user_status_in_keycloak(keycloak_id, is_active)
            except Exception as e:
                logger.error(f"Failed to update user status {keycloak_id} in Keycloak: {e}")
                return False
            
            # Обновляем статус в auth-db
            success = await auth_service.update_user_in_auth_db(
                keycloak_id=keycloak_id,
                update_data={"is_active": is_active},
                source_service=source_service,
                correlation_id=correlation_id
            )
            
            if not success:
                logger.warning(f"User {keycloak_id} not found in auth-db")
                return False
            
            # Публикуем подтверждение изменения статуса
            await auth_service.event_service.publish_user_status_changed(
                keycloak_id=keycloak_id,
                user_id=user_data.get("user_id"),
                is_active=is_active,
                reason=user_data.get("reason"),
                correlation_id=correlation_id,
                source_service=source_service
            )
            
            logger.info(f"Status change for {keycloak_id} processed and confirmed")
            return True
            
    except Exception as e:
        logger.error(f"Error handling user status change request: {e}", exc_info=True)
        return False

async def handle_user_roles_update_requested(event: Dict[str, Any]) -> bool:
    """Обработка события запроса обновления ролей пользователя из user-service"""
    try:
        from shared.events.schemas import BaseEvent
        base_event = BaseEvent(**event)
        
        # Проверяем, не обрабатывали ли мы уже это событие
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed by auth-service")
            return True
        
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        roles = user_data.get("roles", [])
        correlation_id = base_event.correlation_id
        source_service = base_event.source_service
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in user roles update request")
            return False
        
        logger.info(f"Processing roles update request for {keycloak_id} from {source_service}: {roles}")
        
        async with async_session_factory() as session:
            from app.services.keycloak_client import KeycloakClient
            kc_client = KeycloakClient()
            saga_worker = get_saga_worker()  # Получаем saga_worker
            auth_service = AuthService(session, kc_client, saga_worker)  # Передаём все три аргумента
            
            # Обновляем роли в Keycloak
            try:
                kc_client.update_user_roles_in_keycloak(keycloak_id, roles)
                logger.info(f"User {keycloak_id} roles updated in Keycloak: {roles}")
            except Exception as e:
                logger.error(f"Failed to update user roles {keycloak_id} in Keycloak: {e}")
                return False
            
            # Публикуем подтверждение обновления ролей
            await auth_service.event_service.publish_user_roles_updated(
                keycloak_id=keycloak_id,
                user_id=user_data.get("user_id"),
                roles=roles,
                old_roles=user_data.get("old_roles", []),
                correlation_id=correlation_id,
                source_service=source_service
            )
            
            logger.info(f"Roles update for {keycloak_id} processed and confirmed")
            return True
            
    except Exception as e:
        logger.error(f"Error handling user roles update request: {e}", exc_info=True)
        return False

async def handle_user_deletion_requested(event: Dict[str, Any]) -> bool:
    """Обработка события запроса удаления пользователя из user-service"""
    try:
        from shared.events.schemas import BaseEvent
        base_event = BaseEvent(**event)
        
        # Проверяем, не обрабатывали ли мы уже это событие
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed by auth-service")
            return True
        
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        correlation_id = base_event.correlation_id
        source_service = base_event.source_service
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in user deletion request")
            return False
        
        logger.info(f"Processing deletion request for {keycloak_id} from {source_service}")
        
        async with async_session_factory() as session:
            from app.services.keycloak_client import KeycloakClient
            kc_client = KeycloakClient()
            saga_worker = get_saga_worker()  # Получаем saga_worker
            auth_service = AuthService(session, kc_client, saga_worker)  # Передаём все три аргумента
            
            # Удаляем из Keycloak
            try:
                success = kc_client.delete_user_from_keycloak(keycloak_id)
                if success:
                    logger.info(f"User {keycloak_id} deleted from Keycloak")
                else:
                    logger.warning(f"User {keycloak_id} not found in Keycloak or already deleted")
            except Exception as e:
                logger.error(f"Failed to delete user {keycloak_id} from Keycloak: {e}")
                # Продолжаем даже если удаление из Keycloak не удалось
            
            # Удаляем из auth-db - событие будет опубликовано внутри этого метода
            success = await auth_service.delete_user_from_auth_db(
                keycloak_id=keycloak_id,
                correlation_id=correlation_id,
                source_service=source_service
            )
            
            if not success:
                logger.warning(f"User {keycloak_id} not found in auth-db or already deleted")
                # Возвращаем True, так как пользователь уже удален
                return True
            
            logger.info(f"Deletion for {keycloak_id} processed and confirmed")
            return True
            
    except Exception as e:
        logger.error(f"Error handling user deletion request: {e}", exc_info=True)
        return False

async def handle_user_profile_created_ack(event: Dict[str, Any]) -> bool:
    """Просто подтверждаем получение события создания профиля"""
    try:
        from shared.events.schemas import BaseEvent
        base_event = BaseEvent(**event)
        
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed by auth-service")
            return True
        
        logger.debug(f"Received USER_PROFILE_CREATED event from {base_event.source_service}")
        return True
    except Exception as e:
        logger.error(f"Error handling USER_PROFILE_CREATED event: {e}")
        return False

async def register(consumer):
    """Регистрация consumers для событий от user-service"""
    try:
        # Регистрируем обработчики для REQUEST событий
        await consumer.consume_user_events(
            event_type=EventType.USER_PROFILE_UPDATE_REQUESTED,
            callback=handle_user_profile_update_requested
        )
        
        await consumer.consume_user_events(
            event_type=EventType.USER_STATUS_CHANGE_REQUESTED,
            callback=handle_user_status_change_requested
        )
        
        await consumer.consume_user_events(
            event_type=EventType.USER_ROLES_UPDATE_REQUESTED,
            callback=handle_user_roles_update_requested
        )
        
        await consumer.consume_user_events(
            event_type=EventType.USER_DELETION_REQUESTED,
            callback=handle_user_deletion_requested
        )
        
        # Также обрабатываем подтверждения от user-service
        await consumer.consume_user_events(
            event_type=EventType.USER_PROFILE_CREATED,
            callback=handle_user_profile_created_ack
        )
        
        logger.info("User event consumers registered successfully")
    except Exception as e:
        logger.error(f"Failed to register user consumers: {e}", exc_info=True)
        raise