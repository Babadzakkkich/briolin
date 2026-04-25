import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any, List
from pathlib import Path

from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import SmtpConnectionError, TemplateNotFoundError, SendEmailError
from app.schemas.email import EmailType


class EmailService:
    """Сервис для отправки email через SMTP"""
    
    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_email = settings.from_email
        self.use_tls = settings.use_tls
        
        self.templates_dir = Path(__file__).parent.parent / "templates"
        
        # Режим отладки - если нет логина/пароля (как в MailHog)
        self.mock_mode = not self.smtp_user and not self.smtp_password
        
        logger.info(f"SMTP configured: host={self.smtp_host}, port={self.smtp_port}, user={self.smtp_user or '(none)'}")
        if self.mock_mode:
            logger.info("Running with MailHog or anonymous SMTP - emails will be captured")
    
    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Рендеринг HTML шаблона"""
        template_path = self.templates_dir / f"{template_name}.html"
        
        if not template_path.exists():
            raise TemplateNotFoundError(f"Template {template_name} not found")
        
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
        
        for key, value in context.items():
            template = template.replace(f"{{{{ {key} }}}}", str(value))
        
        return template
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """Отправка email через SMTP"""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email
            
            msg.attach(MIMEText(body, "plain"))
            
            if html_body:
                msg.attach(MIMEText(html_body, "html"))
            
            # Подключение к SMTP
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            
            # Логин только если есть учетные данные
            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    async def send_template_email(
        self,
        to_email: str,
        template_name: EmailType,
        context: Dict[str, Any]
    ) -> bool:
        """Отправка email с использованием шаблона"""
        templates = {
            EmailType.WELCOME: {
                "subject": "Welcome to Briolin!",
                "body_template": "welcome"
            },
            EmailType.LOGIN: {
                "subject": "New Login to Your Account",
                "body_template": "login"
            },
            EmailType.TEST_COMPLETE: {
                "subject": f"Your Test Results: {context.get('test_name', 'Test')}",
                "body_template": "test_results"
            },
            EmailType.VERIFICATION: {
                "subject": "Email Verification Code",
                "body_template": "verification"
            },
            EmailType.PASSWORD_RESET: {
                "subject": "Password Reset Code",
                "body_template": "password_reset"
            },
            EmailType.PASSWORD_RESET_CONFIRMATION: {
                "subject": "Password Reset Confirmation",
                "body_template": "password_reset_confirmation"
            }
        }
        
        if template_name not in templates:
            raise TemplateNotFoundError(f"Template {template_name} not configured")
        
        template_info = templates[template_name]
        
        # Рендеринг HTML (если шаблон существует)
        html_body = None
        try:
            html_body = self._render_template(template_info["body_template"], context)
        except TemplateNotFoundError:
            logger.warning(f"Template {template_info['body_template']} not found, using text only")
        
        # Генерация текстовой версии
        body = self._generate_text_body(template_name, context)
        
        return await self.send_email(
            to_email=to_email,
            subject=template_info["subject"],
            body=body,
            html_body=html_body
        )
    
    def _generate_text_body(self, template_name: EmailType, context: Dict[str, Any]) -> str:
        """Генерация текстовой версии письма"""
        name = context.get("name", "User")
        
        if template_name == EmailType.WELCOME:
            return f"""
Hello {name},

Welcome to Briolin! We're excited to have you on board.

Your account has been successfully created.

Best regards,
Briolin Team
"""
        
        elif template_name == EmailType.LOGIN:
            timestamp = context.get("timestamp", "recently")
            return f"""
Hello {name},

A new login was detected to your account at {timestamp}.

If this was you, you can ignore this email.
If this wasn't you, please contact support immediately.

Best regards,
Briolin Team
"""
        
        elif template_name == EmailType.TEST_COMPLETE:
            test_name = context.get("test_name", "Test")
            score = context.get("score", 0)
            total = context.get("total", 0)
            percentage = context.get("percentage", 0)
            
            return f"""
Hello {name},

You have completed the test "{test_name}".

Your score: {score} / {total}
Percentage: {percentage}%

You can view detailed results in your profile.

Best regards,
Briolin Team
"""
        
        elif template_name == EmailType.VERIFICATION:
            code = context.get("code", "000000")
            return f"""
Hello {name},

Your verification code is: {code}

This code expires in 15 minutes.

If you didn't request this, please ignore this email.

Best regards,
Briolin Team
"""
        
        elif template_name == EmailType.PASSWORD_RESET:
            code = context.get("code", "000000")
            return f"""
Hello {name},

You requested to reset your password. Your verification code is: {code}

This code expires in 15 minutes.

If you didn't request this, please ignore this email.

Best regards,
Briolin Team
"""
        
        elif template_name == EmailType.PASSWORD_RESET_CONFIRMATION:
            timestamp = context.get("timestamp", "recently")
            return f"""
Hello {name},

Your password has been successfully reset at {timestamp}.

If you did not perform this action, please contact support immediately.

Best regards,
Briolin Team
"""
        
        return ""
    
    async def send_test_email(self) -> bool:
        """Отправка тестового email"""
        return await self.send_email(
            to_email="test@briolin.local",
            subject="Test Email from Briolin",
            body="This is a test email from Briolin Email Service."
        )
    
    def get_available_templates(self) -> List[str]:
        """Список доступных шаблонов"""
        if not self.templates_dir.exists():
            return []
        return [f.stem for f in self.templates_dir.glob("*.html")]