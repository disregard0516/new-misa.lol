"""The dead-links sweep (v3.125): the owner asks, the server knocks on every link on their page.

  POST /api/v1/me/links/check → {"checked": n, "results": [{id, url, ok, status, note}]}
At most 20 links, five at a time, 6 s each, HEAD first then GET when a host won't HEAD; 2xx and 3xx (followed) are fine.
Three sweeps per ten minutes per account — it's a courtesy to the hosts on the other end.
"""
from __future__ import annotations

import asyncio
import re
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.rate_limit import rate_limit
from app.core.sessions import get_user_from_request
from app.db import data_api
from app.models import User

router = APIRouter(tags=["links"])
MAX_LINKS = 20
TIMEOUT = 6.0
UA = "misa.lol link check (https://misa.lol)"
PRIVATE_HOST = re.compile(r"^(localhost|127\.|10\.|192\.168\.|169\.254\.|0\.|\[?::1\]?$|172\.(1[6-9]|2\d|3[01])\.)", re.I)


async def require_user(request: Request) -> User:
    user = await get_user_from_request(request)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    return user


def link_url(social: dict) -> str | None:
    """The URL the page would send a visitor to, or None for things that aren't web links (email, text-only rows)."""
    if not social.get("enabled") or social.get("displayMode") == "text":
        return None
    value = str(social.get("value") or "").strip()
    if not value or value.startswith("mailto:") or (str(social.get("platform") or "").lower() == "email" and "@" in value):
        return None
    url = value if value.startswith(("http://", "https://")) else "https://" + value
    try:
        host = httpx.URL(url).host
    except Exception:
        return None
    if not host or PRIVATE_HOST.match(host):
        return None
    return url


async def check_url(client: httpx.AsyncClient, url: str) -> tuple[bool, int | None, str]:
    """(ok, status, note). Split out so tests can stub the network."""
    try:
        r = await client.head(url)
        if r.status_code in (405, 403, 404, 501) or r.status_code >= 500:
            r = await client.get(url)
        code = r.status_code
        if code < 400:
            return True, code, "fine"
        if code == 404:
            return False, code, "404 — this one's dead"
        if code in (401, 403):
            return True, code, f"{code} — it answers, but wants a login or blocks robots"
        if code == 429:
            return True, code, "429 — the host is rate-limiting; probably fine"
        return False, code, f"{code} — the host says no"
    except httpx.TimeoutException:
        return False, None, "timed out — slow or gone"
    except httpx.HTTPError as e:
        return False, None, f"can't reach it ({type(e).__name__})"


@router.post("/me/links/check")
async def check_links(user: Annotated[User, Depends(require_user)]) -> dict[str, Any]:
    await rate_limit(f"rl:lc:{user.id}", 3, 600)
    try:
        profile = await data_api.get_profile(user.id) or {}
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not load your page.") from None
    targets = []
    for s in (profile.get("socials") or [])[:60]:
        if isinstance(s, dict):
            url = link_url(s)
            if url:
                targets.append((str(s.get("id") or ""), url))
        if len(targets) >= MAX_LINKS:
            break
    sem = asyncio.Semaphore(5)
    results: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True, headers={"User-Agent": UA}, max_redirects=5) as client:
        async def one(sid: str, url: str) -> None:
            async with sem:
                ok, code, note = await check_url(client, url)
                results.append({"id": sid, "url": url, "ok": ok, "status": code, "note": note})
        await asyncio.gather(*(one(sid, url) for sid, url in targets))
    order = {sid: i for i, (sid, _) in enumerate(targets)}
    results.sort(key=lambda r: order.get(r["id"], 99))
    return {"checked": len(results), "results": results}
