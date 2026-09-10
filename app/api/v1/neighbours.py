"""Neighbours (v3.144): who this page names that names it back.

  GET /api/v1/neighbours/{username}   the mutual list, resolved and cached for ten minutes
A name alone does nothing; only pages that name each other appear. Nothing here is writable by a visitor.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from app.core import neighbours
from app.core.rate_limit import client_ip, rate_limit
from app.core.security import USERNAME_RE
from app.db import data_api

router = APIRouter(tags=["neighbours"])


@router.get("/neighbours/{username}")
async def read_neighbours(username: str, request: Request) -> dict:
    slug = username.strip().lower()
    if not USERNAME_RE.match(slug):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such page.")
    await rate_limit(f"rl:nb:{client_ip(request)}", 30, 300)
    try:
        user = await data_api.find_user(username=slug)
        if not user or user.currently_suspended:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such page.")
        profile = await data_api.get_profile(user.id) or {}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Can't look right now.") from None
    names = neighbours.clean((profile.get("settings") or {}).get("neighbours"), slug)
    if not names:
        return {"neighbours": []}
    cached = await neighbours.peek(user.id)
    if cached is not None:
        return {"neighbours": cached}
    return {"neighbours": await neighbours.resolve(user.id, slug, names, data_api.find_user, data_api.get_profile)}
