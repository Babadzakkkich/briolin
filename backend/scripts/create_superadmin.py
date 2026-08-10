#!/usr/bin/env python3
"""
Скрипт инициализации супер-администратора Briolin.
Поддерживает автоматический режим через переменные окружения и интерактивный режим.

Автоматический режим (через env vars):
    SUPERADMIN_EMAIL=admin@admin.com \
    SUPERADMIN_USERNAME=superadmin \
    SUPERADMIN_PASSWORD=Superadmin228! \
    python scripts/create_superadmin.py

    или просто:
    python scripts/create_superadmin.py  # если env vars уже установлены

Интерактивный режим:
    python scripts/create_superadmin.py --interactive

Тестовый прогон:
    python scripts/create_superadmin.py --dry-run
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path
from getpass import getpass
from typing import Optional
import logging

# Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Импортируем конфигурации сервисов
from app.core.config import settings as auth_settings
from app.core.logger import logger as auth_logger
from app.database.session import async_session_factory as auth_session_factory
from app.database.models import User as AuthUser
from app.services.keycloak_client import KeycloakClient
from shared.schemas.shared import UserRole

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("briolin.init")

# Имена переменных окружения
ENV_EMAIL = "SUPERADMIN_EMAIL"
ENV_USERNAME = "SUPERADMIN_USERNAME"
ENV_PASSWORD = "SUPERADMIN_PASSWORD"


class SuperAdminInitError(Exception):
    """Ошибка инициализации супер-админа"""
    pass


class SuperAdminInitializer:
    """Инициализатор супер-администратора"""
    
    def __init__(self):
        self.keycloak_client: Optional[KeycloakClient] = None
        self._dry_run = False
    
    def _get_keycloak_client(self) -> KeycloakClient:
        """Ленивая инициализация Keycloak клиента"""
        if self.keycloak_client is None:
            self.keycloak_client = KeycloakClient()
        return self.keycloak_client
    
    def validate_password(self, password: str) -> bool:
        """Валидация сложности пароля"""
        if len(password) < 12:
            logger.error("Password must be at least 12 characters")
            return False
        if not any(c.isupper() for c in password):
            logger.error("Password must contain uppercase letter")
            return False
        if not any(c.islower() for c in password):
            logger.error("Password must contain lowercase letter")
            return False
        if not any(c.isdigit() for c in password):
            logger.error("Password must contain digit")
            return False
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            logger.error("Password must contain special character")
            return False
        return True
    
    async def create_in_keycloak(
        self, 
        email: str, 
        username: str, 
        password: str
    ) -> str:
        """
        Создает пользователя в Keycloak с ролью admin.
        
        Returns:
            keycloak_id: ID созданного пользователя
        """
        logger.info(f"Creating user in Keycloak: {email}")
        
        if self._dry_run:
            logger.info("[DRY RUN] Would create Keycloak user")
            return "dry-run-keycloak-id"
        
        kc_client = self._get_keycloak_client()
        
        try:
            # Создаём пользователя с компенсацией
            keycloak_id, compensations = kc_client.create_user_with_compensation(
                email=email,
                username=username,
                password=password,
                role=UserRole.ADMIN.value  # <-- Явно админ
            )
            
            logger.info(f"Created Keycloak user: {keycloak_id}")
            return keycloak_id
            
        except Exception as e:
            logger.error(f"Failed to create Keycloak user: {e}")
            raise SuperAdminInitError(f"Keycloak creation failed: {e}")
    
    async def create_in_auth_db(
        self, 
        keycloak_id: str, 
        email: str
    ) -> int:
        """
        Создает запись в auth-db.
        
        Returns:
            user_id: ID созданного пользователя
        """
        logger.info(f"Creating user in auth-db: {email}")
        
        if self._dry_run:
            logger.info("[DRY RUN] Would create auth-db record")
            return 1
        
        async with auth_session_factory() as session:
            # Проверяем, нет ли уже такого пользователя по keycloak_id
            existing = await session.execute(
                select(AuthUser).where(AuthUser.keycloak_id == keycloak_id)
            )
            if existing.scalar_one_or_none():
                raise SuperAdminInitError(f"User with keycloak_id {keycloak_id} already exists in auth-db")
            
            # Дополнительно проверяем email на уникальность
            existing_email = await session.execute(
                select(AuthUser).where(AuthUser.email == email)
            )
            if existing_email.scalar_one_or_none():
                raise SuperAdminInitError(f"User with email {email} already exists in auth-db")
            
            user = AuthUser(
                keycloak_id=keycloak_id,
                email=email,
                is_active=True
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            logger.info(f"Created auth-db user: ID {user.id}")
            return user.id
    
    async def trigger_user_service_profile(
        self, 
        keycloak_id: str,
        email: str,
        username: str
    ) -> bool:
        """
        Триггерит создание профиля в user-service через событие.
        """
        logger.info(f"Triggering user-service profile creation...")
        
        if self._dry_run:
            logger.info("[DRY RUN] Would publish USER_REGISTERED event")
            return True
        
        try:
            from app.services.event_service import get_event_service
            from app.services.rabbitmq import rabbitmq_publisher
            
            # Подключаемся к RabbitMQ
            await rabbitmq_publisher.connect()
            
            event_service = get_event_service()
            
            success = await event_service.publish_user_registered(
                keycloak_id=keycloak_id,
                email=email,
                username=username,
                role=UserRole.ADMIN.value
            )
            
            if success:
                logger.info("Published USER_REGISTERED event to user-service")
                await asyncio.sleep(2)
            else:
                logger.warning("Failed to publish event, but user created in Keycloak and auth-db")
            
            await rabbitmq_publisher.disconnect()
            return success
            
        except Exception as e:
            logger.warning(f"Could not trigger user-service (non-critical): {e}")
            return False
    
    async def initialize(
        self,
        email: str,
        username: str,
        password: str,
        dry_run: bool = False
    ) -> dict:
        """
        Полная инициализация супер-админа.
        
        Returns:
            dict с результатами операции
        """
        self._dry_run = dry_run
        
        logger.info("=" * 50)
        logger.info("BRIOLIN SUPERADMIN INITIALIZATION")
        logger.info("=" * 50)
        
        if dry_run:
            logger.info("DRY RUN MODE - no changes will be made")
        
        result = {
            "success": False,
            "email": email,
            "username": username,
            "keycloak_id": None,
            "auth_db_id": None,
            "user_service_synced": False,
            "errors": []
        }
        
        try:
            # 1. Валидация пароля
            if not self.validate_password(password):
                raise SuperAdminInitError("Password validation failed")
            
            # 2. Создаём в Keycloak
            keycloak_id = await self.create_in_keycloak(email, username, password)
            result["keycloak_id"] = keycloak_id
            
            # 3. Создаём в auth-db
            auth_db_id = await self.create_in_auth_db(keycloak_id, email)
            result["auth_db_id"] = auth_db_id
            
            # 4. Триггерим user-service
            synced = await self.trigger_user_service_profile(
                keycloak_id, email, username
            )
            result["user_service_synced"] = synced
            
            result["success"] = True
            logger.info("=" * 50)
            logger.info("SUPERADMIN CREATED SUCCESSFULLY")
            logger.info(f"Email: {email}")
            logger.info(f"Username: {username}")
            logger.info(f"Keycloak ID: {keycloak_id}")
            logger.info(f"Auth DB ID: {auth_db_id}")
            logger.info("=" * 50)
            
            return result
            
        except SuperAdminInitError as e:
            result["errors"].append(str(e))
            logger.error(f"Initialization failed: {e}")
            raise
        except Exception as e:
            result["errors"].append(f"Unexpected error: {e}")
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise SuperAdminInitError(f"Unexpected error: {e}")


def get_env_or_prompt(var_name: str, prompt_text: str, secret: bool = False) -> str:
    """
    Получает значение из переменной окружения или запрашивает у пользователя.
    
    Args:
        var_name: Имя переменной окружения
        prompt_text: Текст для prompt (если env var не установлена)
        secret: Если True, использует getpass для скрытого ввода
    
    Returns:
        Значение переменной
    """
    value = os.environ.get(var_name, "").strip()
    
    if value:
        # Маскируем пароль в логах
        display_value = "***" if secret else value
        logger.info(f"Using {var_name} from environment: {display_value}")
        return value
    
    # Если нет в env, запрашиваем интерактивно
    if secret:
        return getpass(f"{prompt_text}: ")
    else:
        return input(f"{prompt_text}: ").strip()


def validate_email(email: str) -> str:
    """Валидация и нормализация email"""
    email = email.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise SuperAdminInitError(f"Invalid email format: {email}")
    return email


def interactive_mode():
    """Интерактивный режим ввода данных"""
    print("\n" + "=" * 50)
    print("BRIOLIN SUPERADMIN CREATION - INTERACTIVE MODE")
    print("=" * 50 + "\n")
    
    email = input("Email: ").strip()
    email = validate_email(email)
    
    username = input("Username (default: superadmin): ").strip() or "superadmin"
    
    print("\nPassword requirements:")
    print("- At least 12 characters")
    print("- Uppercase and lowercase letters")
    print("- At least one digit")
    print("- At least one special character (!@#$%^&*...)")
    
    while True:
        password = getpass("Password: ")
        confirm = getpass("Confirm password: ")
        
        if password != confirm:
            print("Passwords do not match!")
            continue
        
        if len(password) < 12:
            print("Password too short!")
            continue
        
        break
    
    confirm_create = input(f"\nCreate superadmin '{username}' ({email})? [y/N]: ").lower()
    if confirm_create != 'y':
        print("Cancelled")
        sys.exit(0)
    
    return email, username, password


def auto_mode():
    """
    Автоматический режим через переменные окружения.
    Проверяет обязательные переменные и использует дефолты для опциональных.
    """
    print("\n" + "=" * 50)
    print("BRIOLIN SUPERADMIN CREATION - AUTO MODE")
    print("=" * 50 + "\n")
    
    # Получаем обязательные параметры
    email = os.environ.get(ENV_EMAIL, "").strip()
    if not email:
        raise SuperAdminInitError(
            f"Environment variable {ENV_EMAIL} is required for auto mode. "
            f"Use --interactive for interactive mode."
        )
    email = validate_email(email)
    
    # Опциональные с дефолтами
    username = os.environ.get(ENV_USERNAME, "superadmin").strip()
    if not username:
        username = "superadmin"
    
    password = os.environ.get(ENV_PASSWORD, "").strip()
    if not password:
        raise SuperAdminInitError(
            f"Environment variable {ENV_PASSWORD} is required for auto mode. "
            f"Use --interactive for interactive mode."
        )
    
    # Маскируем пароль в выводе
    print(f"Configuration:")
    print(f"  Email:    {email}")
    print(f"  Username: {username}")
    print(f"  Password: {'*' * len(password)} ({len(password)} chars)")
    print()
    
    return email, username, password


async def main():
    parser = argparse.ArgumentParser(
        description="Initialize Briolin superadmin via environment variables or interactively",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Environment Variables (for auto mode):
  {ENV_EMAIL}      Required. Admin email address
  {ENV_USERNAME}   Optional. Username (default: superadmin)
  {ENV_PASSWORD}   Required. Admin password (min 12 chars)

Examples:
  # Auto mode with env vars
  export {ENV_EMAIL}=admin@briolin.com
  export {ENV_PASSWORD}=SuperSecret123!
  python scripts/create_superadmin.py
  
  # Auto mode (one-liner)
  {ENV_EMAIL}=admin@briolin.com {ENV_PASSWORD}=SuperSecret123! python scripts/create_superadmin.py
  
  # Interactive mode
  python scripts/create_superadmin.py --interactive
  
  # Dry run (test configuration)
  python scripts/create_superadmin.py --dry-run
  
  # Force interactive even with env vars set
  python scripts/create_superadmin.py --interactive --ignore-env
        """
    )
    
    parser.add_argument('--interactive', '-i', action='store_true', 
                       help='Force interactive mode (ignore env vars)')
    parser.add_argument('--ignore-env', action='store_true',
                       help='Ignore environment variables, use interactive mode')
    parser.add_argument('--dry-run', '-d', action='store_true',
                       help='Dry run (no actual changes)')
    parser.add_argument('--email', '-e', help='Admin email (overrides env var)')
    parser.add_argument('--username', '-u', help='Admin username (overrides env var)')
    parser.add_argument('--password', '-p', help='Admin password (overrides env var, insecure)')
    
    args = parser.parse_args()
    
    # Определяем режим работы
    use_interactive = args.interactive or args.ignore_env
    
    # Если есть аргументы командной строки - они имеют приоритет
    if args.email or args.username or args.password:
        # Режим с аргументами командной строки (highest priority)
        if not args.email:
            parser.error("--email required when using command line args")
        if not args.password:
            parser.error("--password required when using command line args")
        
        email = validate_email(args.email)
        username = args.username or "superadmin"
        password = args.password
        
        if args.password:
            print("WARNING: Password from command line is insecure!")
    
    elif use_interactive:
        # Интерактивный режим
        email, username, password = interactive_mode()
    
    else:
        # Автоматический режим через env vars
        try:
            email, username, password = auto_mode()
        except SuperAdminInitError as e:
            print(f"\n❌ {e}")
            print("\nTip: Use --interactive for interactive mode")
            sys.exit(1)
    
    # Запускаем инициализацию
    initializer = SuperAdminInitializer()
    
    try:
        result = await initializer.initialize(
            email=email,
            username=username,
            password=password,
            dry_run=args.dry_run
        )
        
        print(f"\n{'=' * 50}")
        print(f"✅ SUCCESS!")
        print(f"{'=' * 50}")
        print(f"   Email:      {result['email']}")
        print(f"   Username:   {result['username']}")
        print(f"   Keycloak:   {result['keycloak_id']}")
        print(f"   Auth DB:    {result['auth_db_id']}")
        
        if not result['user_service_synced']:
            print(f"\n⚠️  Warning: user-service sync may need manual check")
        
        if args.dry_run:
            print(f"\n[DRY RUN] No actual changes were made")
        
        sys.exit(0)
        
    except SuperAdminInitError as e:
        print(f"\n{'=' * 50}")
        print(f"❌ FAILED: {e}")
        print(f"{'=' * 50}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(130)


if __name__ == "__main__":
    asyncio.run(main())