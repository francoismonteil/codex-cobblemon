from __future__ import annotations

import hashlib
import secrets
from typing import Any, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import RedirectResponse

SESSION_AUTH_KEY = "authenticated"
SESSION_CSRF_KEY = "csrf_token"


def is_authenticated(request: Request) -> bool:
    return bool(request.session.get(SESSION_AUTH_KEY))


def login(request: Request) -> None:
    request.session.clear()
    request.session[SESSION_AUTH_KEY] = True
    request.session[SESSION_CSRF_KEY] = secrets.token_urlsafe(24)


def logout(request: Request) -> None:
    request.session.clear()


def get_csrf_token(request: Request) -> str:
    token = request.session.get(SESSION_CSRF_KEY)
    if not token:
        token = secrets.token_urlsafe(24)
        request.session[SESSION_CSRF_KEY] = token
    return token


def verify_password(provided: str, configured: str) -> bool:
    provided_digest = hashlib.sha256(provided.encode("utf-8")).hexdigest()
    configured_digest = hashlib.sha256(configured.encode("utf-8")).hexdigest()
    return secrets.compare_digest(provided_digest, configured_digest)


def require_login(request: Request) -> None:
    if not is_authenticated(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")


def require_login_redirect(request: Request) -> Optional[RedirectResponse]:
    if is_authenticated(request):
        return None
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


def verify_csrf(request: Request) -> None:
    expected = request.session.get(SESSION_CSRF_KEY)
    provided = request.headers.get("X-CSRF-Token")
    if not expected or not provided or not secrets.compare_digest(str(expected), str(provided)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")


def inject_template_context(request: Request, context: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    payload = dict(context or {})
    payload.update(
        {
            "request": request,
            "csrf_token": get_csrf_token(request),
            "is_authenticated": is_authenticated(request),
        }
    )
    return payload
