from fastapi import APIRouter, Depends, HTTPException, status
from app.services.email_service import EmailService
from app.dependencies import get_email_service
from app.schemas.email import (
    EmailSendRequest,
    EmailResponse,
    EmailTemplate,
    BulkEmailRequest
)

router = APIRouter(prefix="/email", tags=["Email"])


@router.post("/send", response_model=EmailResponse, status_code=status.HTTP_202_ACCEPTED)
async def send_email(
    request: EmailSendRequest,
    service: EmailService = Depends(get_email_service)
):
    """
    Отправка email (синхронно через SMTP)
    """
    result = await service.send_email(
        to_email=request.to,
        subject=request.subject,
        body=request.body,
        html_body=request.html_body
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email"
        )
    
    return EmailResponse(
        success=True,
        message="Email sent",
        to=request.to
    )


@router.post("/send-template", response_model=EmailResponse, status_code=status.HTTP_202_ACCEPTED)
async def send_template_email(
    request: EmailTemplate,
    service: EmailService = Depends(get_email_service)
):
    """
    Отправка email с использованием шаблона
    """
    result = await service.send_template_email(
        to_email=request.to,
        template_name=request.template,
        context=request.context
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email"
        )
    
    return EmailResponse(
        success=True,
        message="Email sent",
        to=request.to
    )


@router.get("/templates")
async def list_templates():
    """Список доступных шаблонов"""
    from app.services.email_service import EmailService
    service = EmailService()
    return {"templates": service.get_available_templates()}


@router.post("/test")
async def test_email(
    service: EmailService = Depends(get_email_service)
):
    """Тестовая отправка email"""
    result = await service.send_test_email()
    return {"success": result}