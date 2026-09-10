"""The replay, for the owner (v3.127).

  GET /api/v1/me/replay   the last visits to your page, each one an ordered little story

Nothing here is public: only the page's owner can read it, and only what `app/core/replay.py` keeps —
no addresses, no user agents, no names. Turn it on with `settings.replay`; with it off the list is empty
because nothing was written.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core import replay
from app.core.rate_limit import rate_limit
from app.core.sessions import get_user_from_request
from app.db import data_api
from app.models import User

router = APIRouter(tags=["replay"])
LIMIT = 10


async def require_user(request: Request) -> User:
    user = await get_user_from_request(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    return user


@router.get("/me/replay")
async def my_replay(user: Annotated[User, Depends(require_user)]) -> dict:
    try:
        await rate_limit(f"rl:rp:{user.id}", 30, 60)
    except HTTPException:
        raise
    on = False
    try:
        profile = await data_api.get_profile(user.id) or {}
        on = bool((profile.get("settings") or {}).get("replay"))
    except Exception:
        on = False
    try:
        visits = await replay.visits(user.id, LIMIT)
    except (RuntimeError, OSError):
        return {"on": on, "visits": [], "unavailable": True}
    return {"on": on, "visits": visits, "kept_for_days": replay.TTL // 86400}
