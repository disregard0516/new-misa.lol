"""The guestbook (v3.117): anyone signs a page; the owner approves, or bins, from the dashboard.

  POST /api/v1/guestbook/{username}      {name, line} — queued for the owner (3 per visitor per hour, one per page a day)
  GET  /api/v1/guestbook/{username}      the approved signatures (what the page shows)
  GET  /api/v1/me/guestbook              pending + approved, for the owner
  POST /api/v1/me/guestbook/{id}/approve
  DELETE /api/v1/me/guestbook/{id}
The page's owner turns the book on with settings.guestbook; a page with it off takes no signatures.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.core import guestbook
from app.core.config import get_settings
from app.core.rate_limit import client_ip, rate_limit
from app.core.security import USERNAME_RE
from app.core.sessions import get_user_from_request
from app.db import data_api
from app.models import User

router = APIRouter(tags=["guestbook"])


async def require_user(request: Request) -> User:
    user = await get_user_from_request(request)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    return user


class Signature(BaseModel):
    name: str = Field(min_length=1, max_length=guestbook.NAME_MAX)
    line: str = Field(min_length=1, max_length=guestbook.LINE_MAX)


async def _owner_with_book(slug: str):
    if not USERNAME_RE.match(slug):
        return None, None
    try:
        user = await data_api.find_user(username=slug)
        if not user or user.currently_suspended:
            return None, None
        profile = await data_api.get_profile(user.id) or {}
    except Exception:
        return None, None
    if not (profile.get("settings") or {}).get("guestbook"):
        return None, None
    return user, profile


@router.post("/guestbook/{username}", status_code=201)
async def sign_page(username: str, payload: Signature, request: Request) -> dict:
    slug = username.strip().lower()
    await rate_limit(f"rl:gb:{client_ip(request)}", 3, 3600)
    name, line = guestbook.clean_name(payload.name), guestbook.clean_line(payload.line)
    if not name or not line:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A name and a line, please.")
    user, _ = await _owner_with_book(slug)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That page has no guestbook.")
    settings = get_settings()
    salt = settings.analytics_salt or settings.data_api_key or "misa"
    try:
        entry = await guestbook.sign(user.id, name, line, guestbook.visitor_key(user.id, client_ip(request), request.headers.get("user-agent", ""), salt))
    except (RuntimeError, OSError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="The guestbook is closed for a moment.") from None
    if entry is None:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="You signed this page today already.")
    try:  # v3.127: the replay, when the owner keeps one
        pr = await data_api.get_profile(user.id) or {}
        if (pr.get("settings") or {}).get("replay"):
            from app.core.analytics import visitor_hash
            from app.core.replay import note as replay_note, phone_like
            ua = request.headers.get("user-agent", "")
            await replay_note(user.id, "sign", visitor_hash(request, salt)[:8], "", phone=phone_like(ua))
    except Exception:
        pass
    return {"ok": True, "message": "Signed — it's in the pile. The owner decides what shows."}


@router.get("/guestbook/{username}")
async def read_book(username: str) -> dict:
    user, _ = await _owner_with_book(username.strip().lower())
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That page has no guestbook.")
    return {"entries": await guestbook.approved(user.id)}


@router.get("/me/guestbook")
async def my_book(user: Annotated[User, Depends(require_user)]) -> dict:
    try:
        return {"pending": await guestbook.pending(user.id), "approved": await guestbook.approved(user.id, guestbook.APPROVED_MAX)}
    except (RuntimeError, OSError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="The guestbook is unavailable right now.") from None


@router.post("/me/guestbook/{entry_id}/approve")
async def approve_entry(entry_id: str, user: Annotated[User, Depends(require_user)]) -> dict:
    e = await guestbook.approve(user.id, entry_id[:32])
    if e is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That signature is gone.")
    return {"ok": True, "entry": e}


@router.delete("/me/guestbook/{entry_id}")
async def delete_entry(entry_id: str, user: Annotated[User, Depends(require_user)]) -> dict:
    if not await guestbook.remove(user.id, entry_id[:32]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That signature is gone.")
    return {"ok": True}
