"""Explore (v3.22): real pages whose owners opted in (settings.listed = true), for the explore page's "real pages" row.

Only what a card needs leaves the server — name, handle, a short bio, three colours, whether there's a badge, how
many links, the view count — never the full config. Cached a minute in Dragonfly so a crawl doesn't hit Postgres.
"""
from __future__ import annotations

import json
import re
from typing import Any

from fastapi import APIRouter

from app.core.analytics import total_views
from app.db import data_api
from app.db.dragonfly import get_dragonfly

router = APIRouter(prefix="/explore", tags=["explore"])
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
CACHE_KEY = "explore:listed"
CACHE_TTL = 60


def _hex(value: Any, fallback: str) -> str:
    return value if isinstance(value, str) and HEX_RE.match(value) else fallback


def card(username: str, config: dict[str, Any], views: int) -> dict[str, Any]:
    profile = config.get("profile") or {}
    settings = config.get("settings") or {}
    socials = [s for s in (config.get("socials") or []) if isinstance(s, dict) and s.get("enabled", True) and s.get("value")]
    badges = [b for b in (config.get("badges") or []) if isinstance(b, dict) and b.get("enabled", True) and b.get("owned", True)]
    return {
        "username": username,
        "name": " ".join(str(profile.get("displayName") or username).split())[:40],
        "bio": " ".join(str(profile.get("description") or "").split())[:120],
        "accent": _hex(settings.get("accentColor"), "#F00646"),
        "bg": _hex(settings.get("backgroundColor"), "#050606"),
        "text": _hex(settings.get("textColor"), "#F2F2F0"),
        "badge": bool(badges),
        "links": [str(s.get("label") or s.get("platform") or "")[:30] for s in socials[:3]],
        "link_count": len(socials),
        "views": views,
    }


@router.get("")
async def listed_pages(limit: int = 24) -> dict[str, Any]:
    limit = max(1, min(limit, 48))
    try:
        cached = await get_dragonfly().get(CACHE_KEY)
        if cached:
            data = json.loads(cached)
            return {"pages": data[:limit], "cached": True}
    except (RuntimeError, OSError, ValueError):
        pass
    try:
        rows = await data_api.list_listed_profiles(48)
    except Exception:
        return {"pages": [], "unavailable": True}
    pages = []
    for row in rows:
        username = str(row.get("username") or "")
        if not username:
            continue
        try:
            views = await total_views(str(row.get("user_id")))
        except Exception:
            views = 0
        pages.append(card(username, row.get("config") or {}, views))
    try:
        await get_dragonfly().set(CACHE_KEY, json.dumps(pages), ex=CACHE_TTL)
    except (RuntimeError, OSError):
        pass
    return {"pages": pages[:limit]}
