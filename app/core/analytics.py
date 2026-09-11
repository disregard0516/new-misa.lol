"""Page analytics (v3.10): views, referrers, link clicks — counted on the server in Dragonfly, never trusted from a client.

Keys (all per user id):
  views:<uid>            total views                                   (no expiry)
  views:<uid>:d:<date>   views on that UTC day                          (expires after 100 days)
  refs:<uid>             hash  referrer host → count                    (kept small: at most 64 hosts)
  clicks:<uid>           hash  social id → count
  geos:<uid>             hash  two-letter country → count               (only ISO-shaped codes, so it can't grow wild)
  seen:<uid>:<visitor>   dedupe marker, 30 minutes                      (one view per visitor per half hour)
A view is one page render by a browser that isn't a known crawler / link-preview bot, and isn't the owner looking at
their own page. `visitor` is a salted hash of the client address + user agent — never the address itself.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlsplit

from fastapi import Request

from app.db.dragonfly import get_dragonfly

BOT_RE = re.compile(r"bot|crawl|spider|slurp|preview|facebookexternalhit|twitterbot|discordbot|telegrambot|whatsapp|slackbot|linkedinbot|embedly|quora|pinterest|curl|wget|python-requests|httpx", re.I)
DEDUPE_SECONDS = 1800
DAILY_TTL = 100 * 24 * 3600
MAX_REF_HOSTS = 64
COUNTRY_RE = re.compile(r"^[A-Z]{2}$")


def _day(d: datetime | None = None) -> str:
    return (d or datetime.now(timezone.utc)).strftime("%Y-%m-%d")


def _visitor(request: Request, salt: str) -> str:
    addr = request.headers.get("cf-connecting-ip") or request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else "")
    ua = request.headers.get("user-agent", "")
    return hashlib.sha256(f"{salt}|{addr}|{ua}".encode()).hexdigest()[:24]


visitor_hash = _visitor  # v3.118: the presence counter marks visitors the same way (no address kept)


def _ref_host(request: Request, own_domain: str) -> str | None:
    ref = request.headers.get("referer", "")
    if not ref:
        return None
    try:
        host = (urlsplit(ref).hostname or "").lower()
    except ValueError:
        return None
    if not host or host == own_domain or host.endswith("." + own_domain):
        return None
    return host[:80]


def _country(request: Request) -> str | None:
    code = (request.headers.get("cf-ipcountry") or request.headers.get("x-vercel-ip-country") or "").strip().upper()
    return code if COUNTRY_RE.match(code) and code != "XX" else None


async def record_view(user_id: str, request: Request, *, salt: str, own_domain: str, viewer_id: str | None = None) -> bool:
    """Count one view for a profile render. False if it didn't count: a bot, the owner's own look, or a repeat within 30 min."""
    if BOT_RE.search(request.headers.get("user-agent", "")):
        return False
    if viewer_id and viewer_id == str(user_id):
        return False
    r = get_dragonfly()
    if not await r.set(f"seen:{user_id}:{_visitor(request, salt)}", "1", nx=True, ex=DEDUPE_SECONDS):
        return False
    day_key = f"views:{user_id}:d:{_day()}"
    pipe = r.pipeline()
    pipe.incr(f"views:{user_id}")
    pipe.incr(day_key)
    pipe.expire(day_key, DAILY_TTL)
    host = _ref_host(request, own_domain)
    if host:
        pipe.hincrby(f"refs:{user_id}", host, 1)
    code = _country(request)
    if code:
        pipe.hincrby(f"geos:{user_id}", code, 1)
    await pipe.execute()
    if host:
        # keep the referrer table small: drop the rarest hosts once it grows past the cap
        n = await r.hlen(f"refs:{user_id}")
        if n > MAX_REF_HOSTS:
            table = await r.hgetall(f"refs:{user_id}")
            for h, _ in sorted(table.items(), key=lambda kv: int(kv[1]))[: n - MAX_REF_HOSTS]:
                await r.hdel(f"refs:{user_id}", h)
    return True


MAX_CLICK_IDS = 64


async def record_click(user_id: str, social_id: str) -> None:
    """Count a click on one of the page's links. The table is capped so random ids can't grow it without bound."""
    sid = re.sub(r"[^A-Za-z0-9_-]", "", social_id)[:64]
    if not sid:
        return
    r = get_dragonfly()
    key = f"clicks:{user_id}"
    if not await r.hexists(key, sid) and await r.hlen(key) >= MAX_CLICK_IDS:
        return
    await r.hincrby(key, sid, 1)


async def total_views(user_id: str) -> int:
    try:
        return int(await get_dragonfly().get(f"views:{user_id}") or 0)
    except (RuntimeError, OSError, ValueError):
        return 0


async def stats(user_id: str, days: int = 14) -> dict[str, Any]:
    r = get_dragonfly()
    today = datetime.now(timezone.utc)
    day_keys = [_day(today - timedelta(days=i)) for i in range(days - 1, -1, -1)]
    pipe = r.pipeline()
    pipe.get(f"views:{user_id}")
    for d in day_keys:
        pipe.get(f"views:{user_id}:d:{d}")
    pipe.hgetall(f"refs:{user_id}")
    pipe.hgetall(f"clicks:{user_id}")
    pipe.hgetall(f"geos:{user_id}")
    res = await pipe.execute()
    total = int(res[0] or 0)
    daily = [[d, int(v or 0)] for d, v in zip(day_keys, res[1 : 1 + days])]
    refs = sorted(((h, int(n)) for h, n in (res[1 + days] or {}).items()), key=lambda kv: -kv[1])[:10]
    clicks = sorted(((sid, int(n)) for sid, n in (res[2 + days] or {}).items()), key=lambda kv: -kv[1])[:20]
    geos = sorted(((c, int(n)) for c, n in (res[3 + days] or {}).items()), key=lambda kv: -kv[1])[:10]
    return {"views": total, "today": daily[-1][1] if daily else 0, "week": sum(v for _, v in daily[-7:]), "daily": daily, "referrers": refs, "clicks": clicks, "countries": geos}


async def forget_user(user_id: str) -> None:
    """Drop everything counted for a user (account deletion)."""
    r = get_dragonfly()
    keys = [f"views:{user_id}", f"refs:{user_id}", f"clicks:{user_id}", f"geos:{user_id}"]
    async for key in r.scan_iter(match=f"views:{user_id}:d:*", count=200):
        keys.append(key)
    async for key in r.scan_iter(match=f"seen:{user_id}:*", count=200):
        keys.append(key)
    if keys:
        await r.delete(*keys)
