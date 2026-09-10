"""Visitor doodles (v3.123): anyone draws on a page's chalkboard; the owner keeps or bins from the dashboard.

  POST /api/v1/doodles/{username}        {strokes, colour} — queued for the owner (3 an hour per address, one a day per page)
  GET  /api/v1/doodles/{username}        the approved drawings, as entries
  GET  /api/v1/me/doodles                pending + approved (each with an `svg`), for the owner
  POST /api/v1/me/doodles/{id}/approve
  DELETE /api/v1/me/doodles/{id}
The owner turns the board on with settings.doodles; a page with it off takes no drawings.
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.core import doodles
from app.core.analytics import visitor_hash
from app.core.config import get_settings
from app.core.rate_limit import client_ip, rate_limit
from app.core.security import USERNAME_RE
from app.core.sessions import get_user_from_request
from app.db import data_api
from app.models import User

router = APIRouter(tags=["doodles"])


async def require_user(request: Request) -> User:
    user = await get_user_from_request(request)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    return user


class Drawing(BaseModel):
    strokes: list[Any] = Field(max_length=doodles.STROKES_MAX)
    colour: str = Field(default="chalk", max_length=12)


async def _owner_with_board(slug: str):
    if not USERNAME_RE.match(slug):
        return None
    try:
        user = await data_api.find_user(username=slug)
        if not user or user.currently_suspended:
            return None
        profile = await data_api.get_profile(user.id) or {}
    except Exception:
        return None
    if not (profile.get("settings") or {}).get("doodles"):
        return None
    return user


def _with_svg(entries: list[dict]) -> list[dict]:
    return [{"id": e["id"], "at": e.get("at", 0), "c": e.get("c", "chalk"), "svg": doodles.svg(e)} for e in entries]


@router.post("/doodles/{username}", status_code=201)
async def draw_on_page(username: str, payload: Drawing, request: Request) -> dict:
    slug = username.strip().lower()
    await rate_limit(f"rl:dd:{client_ip(request)}", 3, 3600)
    cleaned = doodles.clean(payload.strokes, payload.colour)
    if cleaned is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Draw something first.")
    user = await _owner_with_board(slug)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That page has no chalkboard.")
    settings = get_settings()
    salt = settings.analytics_salt or settings.data_api_key or "misa"
    strokes, colour = cleaned
    try:
        entry = await doodles.draw(user.id, strokes, colour, doodles.visitor_key(user.id, visitor_hash(request, salt)))
    except (RuntimeError, OSError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="The chalkboard is put away for a moment.") from None
    if entry is None:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="You drew on this page today already.")
    try:  # v3.127: the replay, when the owner keeps one
        pr = await data_api.get_profile(user.id) or {}
        if (pr.get("settings") or {}).get("replay"):
            from app.core.replay import note as replay_note, phone_like
            await replay_note(user.id, "draw", visitor_hash(request, salt)[:8], "", phone=phone_like(request.headers.get("user-agent", "")))
    except Exception:
        pass
    return {"ok": True, "message": "Chalked — the owner decides what stays."}


@router.get("/doodles/{username}")
async def read_board(username: str) -> dict:
    user = await _owner_with_board(username.strip().lower())
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That page has no chalkboard.")
    return {"entries": _with_svg(await doodles.approved(user.id))}


@router.get("/me/doodles")
async def my_board(user: Annotated[User, Depends(require_user)]) -> dict:
    try:
        return {"pending": _with_svg(await doodles.pending(user.id)), "approved": _with_svg(await doodles.approved(user.id, doodles.APPROVED_MAX))}
    except (RuntimeError, OSError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="The chalkboard is unavailable right now.") from None


@router.post("/me/doodles/{entry_id}/approve")
async def approve_drawing(entry_id: str, user: Annotated[User, Depends(require_user)]) -> dict:
    e = await doodles.approve(user.id, entry_id[:32])
    if e is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That drawing is gone.")
    return {"ok": True, "entry": _with_svg([e])[0]}


@router.delete("/me/doodles/{entry_id}")
async def delete_drawing(entry_id: str, user: Annotated[User, Depends(require_user)]) -> dict:
    if not await doodles.remove(user.id, entry_id[:32]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That drawing is gone.")
    return {"ok": True}
