from app.services.email_service import EmailService


# Singleton для EmailService
_email_service = None


def get_email_service() -> EmailService:
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service