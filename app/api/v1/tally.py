"""The tally (v3.136): the page asks; the visitors answer; everyone sees the count.

  POST /api/v1/tally/{username}   {choice} — count one answer (10 an hour per address, one per question)
  GET  /api/v1/tally/{username}   the question, the answers and the counts
The owner sets it with settings.tally {q, options}. Rewording either starts a clean count. Nothing about who
answered is kept — only how many picked each answer.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.core import tally
from app.core.config import get_settings
from app.core.rate_limit import client_ip, rate_limit
from app.core.security import USERNAME_RE
from app.db import data_api

router = APIRouter(tags=["tally"])


class Choice(BaseModel):
    choice: int = Field(ge=0, le=tally.OPTS_MAX - 1)


async def _asking(slug: str):
    """The page's owner and the question it is asking, or None when it asks nothing."""
    if not USERNAME_RE.match(slug):
        return None
    try:
        user = await data_api.find_user(username=slug)
        if not user or user.currently_suspended:
            return None
        profile = await data_api.get_profile(user.id) or {}
    except Exception:
        return None
    asked = tally.clean((profile.get("settings") or {}).get("tally"))
    return None if asked is None else (user, asked)


@router.get("/tally/{username}")
async def read_tally(username: str) -> dict:
    found = await _asking(username.strip().lower())
    if found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That page isn't asking anything.")
    user, (question, options, qid) = found
    return {"q": question, "options": options, "counts": await tally.counts(user.id, qid, len(options))}


@router.post("/tally/{username}", status_code=201)
async def answer_tally(username: str, payload: Choice, request: Request) -> dict:
    found = await _asking(username.strip().lower())
    await rate_limit(f"rl:tl:{client_ip(request)}", 10, 3600)
    if found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That page isn't asking anything.")
    user, (question, options, qid) = found
    if payload.choice >= len(options):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="That isn't one of the answers.")
    settings = get_settings()
    salt = settings.analytics_salt or settings.data_api_key or "misa"
    try:
        counts = await tally.vote(user.id, qid, payload.choice, len(options),
                                  tally.visitor_key(user.id, qid, client_ip(request), request.headers.get("user-agent", ""), salt))
    except (RuntimeError, OSError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Can't count that right now.") from None
    if counts is None:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="You've already answered this one.")
    return {"ok": True, "q": question, "options": options, "counts": counts}
