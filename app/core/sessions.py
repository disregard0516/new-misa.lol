import json
import secrets
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import Response
from starlette.requests import Request

from app.core.config import Settings, get_settings
from app.core.security import cookie_should_be_secure
from app.db import data_api
from app.db.dragonfly import get_dragonfly
from app.models import User


def _session_key(token: str) -> str:
    return f"session:{token}"


async def create_session(user_id: str, remember: bool = False) -> tuple[str, int]:
    settings = get_settings()
    token = secrets.token_urlsafe(32)
    ttl = settings.session_remember_ttl_seconds if remember else settings.session_ttl_seconds
    payload = {
        "user_id": user_id,
        "remember": remember,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await get_dragonfly().set(_session_key(token), json.dumps(payload), ex=ttl)
    return token, ttl


async def destroy_session(token: str | None) -> None:
    if not token:
        return
    await get_dragonfly().delete(_session_key(token))


async def load_session(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    raw = await get_dragonfly().get(_session_key(token))
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) and data.get("user_id") else None


async def touch_session(token: str, remember: bool) -> None:
    settings = get_settings()
    ttl = settings.session_remember_ttl_seconds if remember else settings.session_ttl_seconds
    await get_dragonfly().expire(_session_key(token), ttl)


def attach_session_cookie(response: Response, request: Request, token: str, ttl: int, settings: Settings) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=ttl,
        path="/",
        httponly=True,
        secure=cookie_should_be_secure(request, settings),
        samesite="lax",
    )


def clear_session_cookie(response: Response, request: Request, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        httponly=True,
        secure=cookie_should_be_secure(request, settings),
        samesite="lax",
    )


async def session_user_id(request: Request) -> str | None:
    """The signed-in user's id without fetching the account — enough to tell a page owner from a visitor."""
    data = await load_session(request.cookies.get(get_settings().session_cookie_name))
    if not data:
        return None
    try:
        return str(UUID(str(data["user_id"])))
    except (KeyError, ValueError):
        return None


async def get_user_from_request(request: Request) -> User | None:
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    data = await load_session(token)
    if not data or not token:
        return None
    try:
        UUID(str(data["user_id"]))
    except ValueError:
        return None
    user = await data_api.get_user(str(data["user_id"]))
    if user is None:
        await destroy_session(token)
        return None
    if user.currently_suspended:
        await destroy_session(token)
        return None
    await touch_session(token, bool(data.get("remember")))
    return user
