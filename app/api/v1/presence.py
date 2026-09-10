"""Live presence (v3.118): a public page asks “how many are here?” and, by asking, counts itself.

  POST /api/v1/presence/{username}        heartbeat → {"here": n}   (n counts the caller)
  POST /api/v1/presence/{username}/leave  beacon on pagehide → 204
Only pages with settings.presence on answer; anything else is a 404 that says nothing about whether the name exists.
Crawlers and link-preview bots are answered but never counted.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.core import presence
from app.core.analytics import BOT_RE, visitor_hash
from app.core.config import get_settings
from app.core.rate_limit import client_ip, rate_limit
from app.core.security import USERNAME_RE
from app.db import data_api

router = APIRouter(tags=["presence"])


async def _owner_with_presence(slug: str):
    if not USERNAME_RE.match(slug):
        return None
    try:
        user = await data_api.find_user(username=slug)
        if not user or user.currently_suspended:
            return None
        profile = await data_api.get_profile(user.id) or {}
    except Exception:
        return None
    if not (profile.get("settings") or {}).get("presence"):
        return None
    return user


def _visitor(request: Request) -> str:
    settings = get_settings()
    return visitor_hash(request, settings.analytics_salt or settings.data_api_key or "misa")


@router.post("/presence/{username}")
async def heartbeat(username: str, request: Request) -> dict:
    slug = username.strip().lower()
    await rate_limit(f"rl:pr:{client_ip(request)}", 40, 60)
    user = await _owner_with_presence(slug)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nothing here.")
    try:
        if BOT_RE.search(request.headers.get("user-agent", "")):
            return {"here": await presence.here(user.id)}
        return {"here": await presence.beat(user.id, _visitor(request))}
    except (RuntimeError, OSError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Nobody's counting right now.") from None


@router.post("/presence/{username}/leave", status_code=204)
async def leave(username: str, request: Request) -> Response:
    slug = username.strip().lower()
    if USERNAME_RE.match(slug):
        try:
            await rate_limit(f"rl:pr:{client_ip(request)}", 40, 60)
            user = await _owner_with_presence(slug)
            if user is not None:
                await presence.leave(user.id, _visitor(request))
        except Exception:
            pass
    return Response(status_code=204)
