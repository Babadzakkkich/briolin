import json
from typing import Dict, Any
from shared.events.schemas import EventType
from app.services.rabbitmq import rabbitmq_consumer
from app.services.auth_service import AuthService
from app.database.session import async_session_factory
from app.core.logger import logger

async def handle_user_profile_created(event: Dict[str, Any]) -> bool:
    """Обработка события создания профиля пользователя из user-service"""
    try:
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        processed_by = event.get("processed_by", [])
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in user profile created event")
            return False
        
        # Проверяем, не обрабатывали ли мы уже это событие
        if "auth-service" in processed_by:
            logger.debug(f"Event already processed by auth-service for {keycloak_id}")
            return True
        
        logger.info(f"User profile created in user-service for {keycloak_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error handling user profile created event: {e}")
        return False

async def handle_user_profile_updated(event: Dict[str, Any]) -> bool:
    """Обработка события обновления профиля пользователя из user-service"""
    try:
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        updated_fields = user_data.get("updated_fields", {})
        source_service = event.get("source_service", "")
        processed_by = event.get("processed_by", [])
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in user profile update event")
            return False
        
        # Проверяем, не обрабатывали ли мы уже это событие
        if "auth-service" in processed_by:
            logger.debug(f"Event already processed by auth-service for {keycloak_id}")
            return True
        
        logger.debug(f"Processing user profile update from {source_service} for {keycloak_id}: {updated_fields}")
        
        async with async_session_factory() as session:
            from app.services.keycloak_client import KeycloakClient
            kc_client = KeycloakClient()
            auth_service = AuthService(session, kc_client)
            
            # Определяем поля, которые нужно обновить в auth-db
            auth_update_fields = {}
            if 'email' in updated_fields:
                auth_update_fields['email'] = updated_fields['email']
            if 'is_active' in updated_fields:
                auth_update_fields['is_active'] = updated_fields['is_active']
            
            if auth_update_fields:
                success = await auth_service.update_user_in_auth_db(
                    keycloak_id=keycloak_id,
                    update_data=auth_update_fields,
                    source_service=source_service
                )
                
                if success:
                    logger.info(f"Updated user {keycloak_id} in auth-db from {source_service}")
                else:
                    logger.warning(f"User {keycloak_id} not found in auth-db")
                
                return success
            else:
                logger.debug(f"No auth-db updates needed for {keycloak_id}")
                return True
            
    except Exception as e:
        logger.error(f"Error handling user profile update event: {e}")
        return False

async def handle_user_status_changed(event: Dict[str, Any]) -> bool:
    """Обработка события изменения статуса пользователя из user-service"""
    try:
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        is_active = user_data.get("is_active")
        source_service = event.get("source_service", "")
        processed_by = event.get("processed_by", [])
        
        if not keycloak_id or is_active is None:
            logger.error("Missing keycloak_id or is_active in user status changed event")
            return False
        
        # Проверяем, не обрабатывали ли мы уже это событие
        if "auth-service" in processed_by:
            logger.debug(f"Event already processed by auth-service for {keycloak_id}")
            return True
        
        logger.debug(f"Processing user status change from {source_service} for {keycloak_id}: {is_active}")
        
        async with async_session_factory() as session:
            from app.services.keycloak_client import KeycloakClient
            kc_client = KeycloakClient()
            auth_service = AuthService(session, kc_client)
            
            success = await auth_service.update_user_in_auth_db(
                keycloak_id=keycloak_id,
                update_data={"is_active": is_active},
                source_service=source_service
            )
            
            if success:
                logger.info(f"Updated user status in auth-db for {keycloak_id} from {source_service}: {is_active}")
            else:
                logger.warning(f"User {keycloak_id} not found in auth-db")
            
            return success
            
    except Exception as e:
        logger.error(f"Error handling user status changed event: {e}")
        return False

async def handle_user_deleted(event: Dict[str, Any]) -> bool:
    """Обработка события удаления пользователя из user-service"""
    try:
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        source_service = event.get("source_service", "")
        processed_by = event.get("processed_by", [])
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in user deletion event")
            return False
        
        # Проверяем, не обрабатывали ли мы уже это событие
        if "auth-service" in processed_by:
            logger.debug(f"Event already processed by auth-service for {keycloak_id}")
            return True
        
        logger.info(f"Processing user deletion event from {source_service} for {keycloak_id}")
        
        async with async_session_factory() as session:
            from app.services.keycloak_client import KeycloakClient
            kc_client = KeycloakClient()
            auth_service = AuthService(session, kc_client)
            
            success = await auth_service.delete_user_from_auth_db(keycloak_id)
            
            if success:
                logger.info(f"User {keycloak_id} deleted from auth-db (triggered by {source_service})")
            else:
                logger.warning(f"User {keycloak_id} not found in auth-db, already deleted")
            
            return success
            
    except Exception as e:
        logger.error(f"Error handling user deletion event: {e}", exc_info=True)
        return False

async def register(consumer):
    """Регистрация consumers для событий от user-service"""
    try:
        await consumer.consume_user_events(
            event_type=EventType.USER_PROFILE_CREATED,
            callback=handle_user_profile_created
        )
        
        await consumer.consume_user_events(
            event_type=EventType.USER_PROFILE_UPDATED,
            callback=handle_user_profile_updated
        )
        
        await consumer.consume_user_events(
            event_type=EventType.USER_STATUS_CHANGED,
            callback=handle_user_status_changed
        )
        
        await consumer.consume_user_events(
            event_type=EventType.USER_DELETED,
            callback=handle_user_deleted
        )
        
        logger.info("User event consumers registered successfully")
    except Exception as e:
        logger.error(f"Failed to register user consumers: {e}", exc_info=True)
        raise