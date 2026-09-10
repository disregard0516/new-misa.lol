"""Weather where you are (v3.125): a block that says “raining in berlin, 11°”. Open-Meteo — free, no key — via the server.

Two lookups, both cached in Dragonfly and never awaited by a page render:
  geo:<name>        the place → (lat, lon, label)     kept 7 days
  wx:<lat>,<lon>    the current conditions             kept 10 minutes (3 on a failure)
`peek()` is for renders (cache only; a cold miss starts a refresh in the background); `get()` is for the page's poll and
awaits the network (2.5 s timeouts, one lookup in flight per place).
"""
from __future__ import annotations

import asyncio
import json
import re
import time
from typing import Any
from urllib.parse import quote_plus

import httpx

from app.db.dragonfly import get_dragonfly

TIMEOUT = 2.5
GEO_TTL = 7 * 24 * 3600
WX_TTL = 600
FAIL_TTL = 180
UA = "misa.lol (https://misa.lol; weather block)"
PLACE_RE = re.compile(r"^[\w .,'’\-]{2,64}$", re.U)
_inflight: set[str] = set()

# WMO weather codes → (what the page says, the icon)
WORDS: dict[int, tuple[str, str]] = {
    0: ("clear", "sun"), 1: ("mostly clear", "sun"), 2: ("partly cloudy", "cloud-sun"), 3: ("overcast", "cloud"),
    45: ("foggy", "fog"), 48: ("foggy", "fog"),
    51: ("drizzle", "rain"), 53: ("drizzle", "rain"), 55: ("drizzle", "rain"), 56: ("freezing drizzle", "rain"), 57: ("freezing drizzle", "rain"),
    61: ("raining", "rain"), 63: ("raining", "rain"), 65: ("pouring", "rain"), 66: ("freezing rain", "rain"), 67: ("freezing rain", "rain"),
    71: ("snowing", "snow"), 73: ("snowing", "snow"), 75: ("heavy snow", "snow"), 77: ("snow grains", "snow"),
    80: ("showers", "rain"), 81: ("showers", "rain"), 82: ("downpour", "rain"), 85: ("snow showers", "snow"), 86: ("snow showers", "snow"),
    95: ("storms", "storm"), 96: ("storms with hail", "storm"), 99: ("storms with hail", "storm"),
}


def clean_place(value: Any) -> str:
    v = re.sub(r"\s+", " ", str(value or "")).strip()
    return v if PLACE_RE.match(v) else ""


def describe(code: int, is_day: bool) -> tuple[str, str]:
    word, icon = WORDS.get(int(code), ("weather", "cloud"))
    if not is_day and icon in ("sun", "cloud-sun"):
        return ("clear night" if code <= 1 else "cloudy night", "moon")
    return word, icon


# v3.130: the sky effect a page wears — the same WMO code, read as weather on the glass rather than words
SKY = {"sun": "clear", "moon": "night", "cloud-sun": "cloud", "cloud": "cloud", "fog": "fog", "rain": "rain", "snow": "snow", "storm": "storm"}


def effect(code: int, is_day: bool) -> str:
    """rain · snow · storm · fog · cloud · clear · night — what to draw over the page.

    `describe()` calls every night sky “moon”, which is fine for words; here it matters whether there are
    clouds in front of it — stars over an overcast night would be a small lie.
    """
    icon = WORDS.get(int(code), ("weather", "cloud"))[1]
    if not is_day and icon in ("sun", "cloud-sun"):
        return "night" if int(code) <= 1 else "cloud"
    return SKY.get(icon, "clear")


def temp(celsius: float, unit: str) -> str:
    if unit == "f":
        return f"{round(celsius * 9 / 5 + 32)}°"
    return f"{round(celsius)}°"


async def fetch_json(url: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, headers={"User-Agent": UA, "Accept": "application/json"}) as client:
            r = await client.get(url)
            if r.status_code != 200:
                return None
            return r.json()
    except (httpx.HTTPError, ValueError):
        return None


async def geocode(place: str) -> dict | None:
    """{lat, lon, label} for a place name — the first match Open-Meteo's geocoder gives."""
    key = f"geo:{place.lower()}"
    r = get_dragonfly()
    try:
        raw = await r.get(key)
        if raw:
            data = json.loads(raw)
            return data or None
    except (RuntimeError, OSError, ValueError):
        pass
    payload = await fetch_json(f"https://geocoding-api.open-meteo.com/v1/search?name={quote_plus(place)}&count=1&language=en&format=json")
    hit = None
    try:
        first = (payload or {}).get("results", [])[0]
        hit = {"lat": round(float(first["latitude"]), 3), "lon": round(float(first["longitude"]), 3), "label": str(first.get("name") or place).lower()[:40]}
    except (IndexError, KeyError, TypeError, ValueError):
        hit = None
    try:
        await r.set(key, json.dumps(hit or {}), ex=GEO_TTL if hit else FAIL_TTL)
    except (RuntimeError, OSError):
        pass
    return hit


async def conditions(lat: float, lon: float) -> dict | None:
    """{code, c, day} right now for a point."""
    key = f"wx:{lat},{lon}"
    r = get_dragonfly()
    try:
        raw = await r.get(key)
        if raw:
            data = json.loads(raw)
            return data or None
    except (RuntimeError, OSError, ValueError):
        pass
    payload = await fetch_json(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code,is_day&timezone=UTC")
    data = None
    try:
        cur = payload["current"]
        data = {"code": int(cur["weather_code"]), "c": float(cur["temperature_2m"]), "day": bool(cur.get("is_day", 1)), "at": int(time.time())}
    except (KeyError, TypeError, ValueError):
        data = None
    try:
        await r.set(key, json.dumps(data or {}), ex=WX_TTL if data else FAIL_TTL)
    except (RuntimeError, OSError):
        pass
    return data


async def lookup(place: str) -> dict | None:
    """Everything the block needs: {label, code, c, day, at} — or None when the place or the weather can't be had."""
    geo = await geocode(place)
    if not geo:
        return None
    wx = await conditions(geo["lat"], geo["lon"])
    if not wx:
        return None
    return {"label": geo["label"], **wx}


async def refresh(place: str) -> dict | None:
    if place in _inflight:
        return None
    _inflight.add(place)
    try:
        return await lookup(place)
    finally:
        _inflight.discard(place)


async def cached(place: str) -> dict | None:
    """The answer if both halves are cached, else None (no network)."""
    r = get_dragonfly()
    try:
        raw = await r.get(f"geo:{place.lower()}")
        geo = json.loads(raw) if raw else None
        if not geo:
            return None
        raw = await r.get(f"wx:{geo['lat']},{geo['lon']}")
        wx = json.loads(raw) if raw else None
        if not wx:
            return None
        return {"label": geo["label"], **wx}
    except (RuntimeError, OSError, ValueError, KeyError, TypeError):
        return None


async def peek(place: str) -> dict | None:
    data = await cached(place)
    if data is None and place not in _inflight:
        try:
            asyncio.get_running_loop().create_task(refresh(place))
        except RuntimeError:
            pass
    return data


async def get(place: str) -> dict | None:
    return await cached(place) or await refresh(place)


def line(data: dict, unit: str = "c", label: str = "") -> tuple[str, str, str]:
    """(“raining in berlin”, “11°”, icon) — the label the owner typed wins over the geocoder's."""
    word, icon = describe(int(data.get("code", 3)), bool(data.get("day", True)))
    place = (label or str(data.get("label") or "")).strip()
    return (f"{word} in {place}" if place else word), temp(float(data.get("c", 0)), unit), icon
