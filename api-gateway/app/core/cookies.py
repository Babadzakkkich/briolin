from typing import Any, Dict, Optional
from fastapi import Response

from app.core.config import settings


def _cookie_kwargs(max_age: Optional[int] = None, httponly: bool = True) -> Dict[str, Any]:
    kwargs: Dict[str, Any] = {
        "httponly": httponly,
        "secure": settings.cookies.secure,
        "samesite": settings.cookies.samesite,
        "path": settings.cookies.path,
    }

    if max_age is not None:
        kwargs["max_age"] = max_age

    if settings.cookies.domain:
        kwargs["domain"] = settings.cookies.domain

    return kwargs


def set_auth_cookies(response: Response, token_data: Dict[str, Any]) -> None:
    """Сохраняет Keycloak access/refresh tokens в HttpOnly cookies."""
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    if access_token:
        response.set_cookie(
            key=settings.cookies.access_cookie_name,
            value=access_token,
            **_cookie_kwargs(
                max_age=int(token_data.get("expires_in") or 0),
                httponly=True,
            ),
        )

    if refresh_token:
        response.set_cookie(
            key=settings.cookies.refresh_cookie_name,
            value=refresh_token,
            **_cookie_kwargs(
                max_age=int(token_data.get("refresh_expires_in") or 0),
                httponly=True,
            ),
        )


def clear_auth_cookies(response: Response) -> None:
    delete_cookie(response, settings.cookies.access_cookie_name)
    delete_cookie(response, settings.cookies.refresh_cookie_name)


def delete_cookie(response: Response, key: str) -> None:
    kwargs: Dict[str, Any] = {
        "path": settings.cookies.path,
        "secure": settings.cookies.secure,
        "samesite": settings.cookies.samesite,
    }

    if settings.cookies.domain:
        kwargs["domain"] = settings.cookies.domain

    response.delete_cookie(key=key, **kwargs)
