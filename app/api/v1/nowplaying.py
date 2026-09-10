"""Now playing (v3.122): what a page's owner is listening to, for the page's 45-second poll.

  GET /api/v1/nowplaying/{username} → {"playing", "track", "artist", "ago"}
Only pages with a now-playing block that names a ListenBrainz user answer; anything else is a 404 that says nothing
about whether the name exists. Answers come from the cache when it's warm, from ListenBrainz when it isn't.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from app.core import nowplaying
from app.core.rate_limit import client_ip, rate_limit
from app.core.security import USERNAME_RE
from app.db import data_api

router = APIRouter(tags=["nowplaying"])


def listenbrainz_user(profile: dict) -> str:
    """The first now-playing block's ListenBrainz name, or ''."""
    blocks = (profile.get("settings") or {}).get("blocks")
    for blk in (blocks if isinstance(blocks, list) else [])[:12]:
        if isinstance(blk, dict) and str(blk.get("type") or "").lower() == "nowplaying" and blk.get("enabled") is not False:
            lb = nowplaying.clean_user(blk.get("lb"))
            if lb:
                return lb
    return ""


@router.get("/nowplaying/{username}")
async def now_playing(username: str, request: Request) -> dict:
    slug = username.strip().lower()
    await rate_limit(f"rl:np:{client_ip(request)}", 30, 60)
    lb = ""
    if USERNAME_RE.match(slug):
        try:
            user = await data_api.find_user(username=slug)
            if user and not user.currently_suspended:
                lb = listenbrainz_user(await data_api.get_profile(user.id) or {})
        except Exception:
            lb = ""
    if not lb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nothing playing here.")
    data = await nowplaying.get(lb)
    if not data or not data.get("track"):
        return {"playing": False, "track": "", "artist": "", "ago": ""}
    playing = bool(data.get("playing"))
    return {"playing": playing, "track": data["track"], "artist": data.get("artist") or "", "ago": "" if playing else nowplaying.ago(int(data.get("at") or 0))}
