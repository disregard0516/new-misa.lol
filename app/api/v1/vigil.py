"""The vigil (v3.134): visitors light a candle on a page; it burns down and goes out on its own.

  POST   /api/v1/vigil/{username}   light one (6 an hour per address, one a day per page)
  GET    /api/v1/vigil/{username}   the candles still lit, oldest first — what the page draws
  DELETE /api/v1/me/vigil           the owner clears their own shelf
The owner turns it on with settings.vigil, whose value is also how long a candle lasts: "6", "12" or "24" hours.
Nothing about who lit a candle is kept — the once-a-day marker is a salted hash, exactly like the guestbook's.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core import vigil
from app.core.config import get_settings
from app.core.rate_limit import client_ip, rate_limit
from app.core.security import USERNAME_RE
from app.core.sessions import get_user_from_request
from app.db import data_api
from app.models import User

router = APIRouter(tags=["vigil"])


async def require_user(request: Request) -> User:
    user = await get_user_from_request(request)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    return user


async def _owner_with_vigil(slug: str):
    """The page's owner and how long its candles burn, or None when the page keeps no vigil."""
    if not USERNAME_RE.match(slug):
        return None
    try:
        user = await data_api.find_user(username=slug)
        if not user or user.currently_suspended:
            return None
        profile = await data_api.get_profile(user.id) or {}
    except Exception:
        return None
    burn = vigil.burn_of((profile.get("settings") or {}).get("vigil"))
    return None if burn is None else (user, burn)


@router.post("/vigil/{username}", status_code=201)
async def light_candle(username: str, request: Request) -> dict:
    found = await _owner_with_vigil(username.strip().lower())
    await rate_limit(f"rl:vg:{client_ip(request)}", 6, 3600)
    if found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That page keeps no vigil.")
    user, burn = found
    settings = get_settings()
    salt = settings.analytics_salt or settings.data_api_key or "misa"
    try:
        candle = await vigil.light(user.id, burn, vigil.visitor_key(user.id, client_ip(request), request.headers.get("user-agent", ""), salt))
    except (RuntimeError, OSError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="The shelf is out of reach for a moment.") from None
    if candle is None:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Yours is already burning. Come back tomorrow.")
    try:  # the replay, when the owner keeps one
        pr = await data_api.get_profile(user.id) or {}
        if (pr.get("settings") or {}).get("replay"):
            from app.core.analytics import visitor_hash
            from app.core.replay import note as replay_note, phone_like
            await replay_note(user.id, "light", visitor_hash(request, salt)[:8], "", phone=phone_like(request.headers.get("user-agent", "")))
    except Exception:
        pass
    return {"ok": True, "candle": candle, "lit": await vigil.lit(user.id), "message": "Lit. It burns itself out."}


@router.get("/vigil/{username}")
async def read_vigil(username: str) -> dict:
    found = await _owner_with_vigil(username.strip().lower())
    if found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That page keeps no vigil.")
    user, burn = found
    return {"burn": burn, "lit": await vigil.lit(user.id)}


@router.delete("/me/vigil")
async def clear_vigil(user: Annotated[User, Depends(require_user)]) -> dict:
    try:
        await vigil.snuff(user.id)
    except (RuntimeError, OSError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="The shelf is out of reach right now.") from None
    return {"ok": True}
