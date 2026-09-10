"""The ask box (v3.128): anyone leaves a question; the owner answers it, and the answer goes on the page.

  POST   /api/v1/asks/{username}         {question} — queued for the owner (3 an hour per address, one a day per page)
  GET    /api/v1/asks/{username}         the answered questions (what the page shows)
  GET    /api/v1/me/asks                 waiting + answered, for the owner
  POST   /api/v1/me/asks/{id}/answer     {answer} — answering is what publishes it
  DELETE /api/v1/me/asks/{id}            bin it, answered or not
The owner turns the box on with settings.asks; a page with it off takes no questions. An unanswered question
is never public.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.core import asks
from app.core.config import get_settings
from app.core.rate_limit import client_ip, rate_limit
from app.core.security import USERNAME_RE
from app.core.sessions import get_user_from_request
from app.db import data_api
from app.models import User

router = APIRouter(tags=["asks"])


async def require_user(request: Request) -> User:
    user = await get_user_from_request(request)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    return user


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=asks.Q_MAX)


class Answer(BaseModel):
    answer: str = Field(min_length=1, max_length=asks.A_MAX)


async def _owner_with_box(slug: str):
    if not USERNAME_RE.match(slug):
        return None
    try:
        user = await data_api.find_user(username=slug)
        if not user or user.currently_suspended:
            return None
        profile = await data_api.get_profile(user.id) or {}
    except Exception:
        return None
    if not (profile.get("settings") or {}).get("asks"):
        return None
    return user


@router.post("/asks/{username}", status_code=201)
async def ask_page(username: str, payload: Question, request: Request) -> dict:
    slug = username.strip().lower()
    await rate_limit(f"rl:ak:{client_ip(request)}", 3, 3600)
    question = asks.clean_question(payload.question)
    if not question:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ask something first.")
    user = await _owner_with_box(slug)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That page has no ask box.")
    settings = get_settings()
    salt = settings.analytics_salt or settings.data_api_key or "misa"
    try:
        entry = await asks.ask(user.id, question, asks.visitor_key(user.id, client_ip(request), request.headers.get("user-agent", ""), salt))
    except (RuntimeError, OSError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="The ask box is shut for a moment.") from None
    if entry is None:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="You asked this page today already.")
    try:  # the replay, when the owner keeps one
        pr = await data_api.get_profile(user.id) or {}
        if (pr.get("settings") or {}).get("replay"):
            from app.core.analytics import visitor_hash
            from app.core.replay import note as replay_note, phone_like
            await replay_note(user.id, "ask", visitor_hash(request, salt)[:8], "", phone=phone_like(request.headers.get("user-agent", "")))
    except Exception:
        pass
    return {"ok": True, "message": "Asked. If they answer it, it shows up on the page."}


@router.get("/asks/{username}")
async def read_asks(username: str) -> dict:
    user = await _owner_with_box(username.strip().lower())
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That page has no ask box.")
    return {"entries": await asks.answered(user.id)}


@router.get("/me/asks")
async def my_asks(user: Annotated[User, Depends(require_user)]) -> dict:
    try:
        return {"waiting": await asks.waiting(user.id), "answered": await asks.answered(user.id, asks.DONE_MAX)}
    except (RuntimeError, OSError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="The ask box is unavailable right now.") from None


@router.post("/me/asks/{entry_id}/answer")
async def answer_question(entry_id: str, payload: Answer, user: Annotated[User, Depends(require_user)]) -> dict:
    eid = entry_id[:32]
    if not asks.clean_answer(payload.answer):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Write an answer — that's what goes on your page.")
    e = await asks.answer(user.id, eid, payload.answer)
    if e is None:                                   # already answered? then this is a rewrite
        e = await asks.edit(user.id, eid, payload.answer)
    if e is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That question is gone.")
    return {"ok": True, "entry": e}


@router.delete("/me/asks/{entry_id}")
async def delete_question(entry_id: str, user: Annotated[User, Depends(require_user)]) -> dict:
    if not await asks.remove(user.id, entry_id[:32]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That question is gone.")
    return {"ok": True}
