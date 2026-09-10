"""Public "report this page" (v3.14) — fills the reports table the admin page reviews.

Anyone can report a page (signed in or not); the reporter's id is kept when known. Five reports per visitor per hour,
a fixed list of reasons, details capped, and the answer never says more than "thanks" — no hints about who exists.
"""
from __future__ import annotations

import re
from typing import Annotated

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.core.rate_limit import client_ip, rate_limit
from app.core.security import USERNAME_RE
from app.core.sessions import get_user_from_request
from app.db import admin_db, data_api

router = APIRouter(prefix="/reports", tags=["reports"])

REASONS = ("spam", "impersonation", "harassment", "illegal", "other")


class ReportRequest(BaseModel):
    username: str = Field(min_length=3, max_length=24)
    reason: str = Field(pattern="^(" + "|".join(REASONS) + ")$")
    details: str = Field(default="", max_length=1000)


@router.post("", status_code=201)
async def report_page(payload: ReportRequest, request: Request) -> dict:
    slug = payload.username.strip().lower()
    if not USERNAME_RE.match(slug):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="That isn't a page name.")
    await rate_limit(f"rl:report:{client_ip(request)}", 5, 3600)
    reporter = await get_user_from_request(request)
    try:
        target = await data_api.find_user(username=slug)
    except Exception:
        target = None
    details = " ".join(payload.details.split())[:1000]
    if target is not None:
        try:
            await admin_db.add_report(reporter.id if reporter else None, target.id, slug, payload.reason, details)
        except (RuntimeError, OSError):
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Reports are unavailable right now.") from None
    # an unknown name gets the same answer as a real one
    return {"ok": True, "message": "Thanks — someone will look at it."}
