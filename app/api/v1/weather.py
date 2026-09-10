"""Weather where you are (v3.125): the page's poll for its weather block.

  GET /api/v1/weather/{username} → {"line": "raining in berlin", "temp": "11°", "icon": "rain", "sky": "rain"}
The `sky` is v3.130: what a page with the sky effect on should be drawing over itself right now.
Only pages with a weather block answer (404 otherwise, saying nothing about the name); the answer is the cache when it's
warm and Open-Meteo when it isn't.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from app.core import weather
from app.core.rate_limit import client_ip, rate_limit
from app.core.security import USERNAME_RE
from app.db import data_api

router = APIRouter(tags=["weather"])


def weather_block(profile: dict) -> dict | None:
    """The first enabled weather block with a usable place, or None."""
    blocks = (profile.get("settings") or {}).get("blocks")
    for blk in (blocks if isinstance(blocks, list) else [])[:12]:
        if isinstance(blk, dict) and str(blk.get("type") or "").lower() == "weather" and blk.get("enabled") is not False:
            place = weather.clean_place(blk.get("city"))
            if place:
                return {"place": place, "unit": "f" if str(blk.get("unit") or "c").lower() == "f" else "c", "label": str(blk.get("text") or "").strip()[:40]}
    return None


@router.get("/weather/{username}")
async def page_weather(username: str, request: Request) -> dict:
    slug = username.strip().lower()
    await rate_limit(f"rl:wx:{client_ip(request)}", 30, 60)
    blk = None
    if USERNAME_RE.match(slug):
        try:
            user = await data_api.find_user(username=slug)
            if user and not user.currently_suspended:
                blk = weather_block(await data_api.get_profile(user.id) or {})
        except Exception:
            blk = None
    if not blk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No weather here.")
    data = await weather.get(blk["place"])
    if not data:
        return {"line": "", "temp": "", "icon": "", "sky": ""}
    text, t, icon = weather.line(data, blk["unit"], blk["label"])
    return {"line": text, "temp": t, "icon": icon, "sky": weather.effect(int(data.get("code", 3)), bool(data.get("day", True)))}
