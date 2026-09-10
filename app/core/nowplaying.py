"""Now playing (v3.122): a block that says what the owner is listening to, live, from ListenBrainz — no API key needed.

A "now playing" block carries `lb`, a ListenBrainz username. The page never waits on the network: the profile route reads
the cache (`np:<user>`, 45 s) and, when it's cold, starts a refresh in the background and shows the typed text meanwhile;
the page polls `GET /api/v1/nowplaying/{username}` every 45 s and swaps the line live. A block without `lb` is just words.

ListenBrainz's public API: /1/user/<name>/playing-now (what's on right now) and /1/user/<name>/listens?count=1 (the last
listen, with its timestamp). Both are open, both are read with a 2.5 s timeout and never more than once a cache window.
"""
from __future__ import annotations

import asyncio
import json
import re
import time
from typing import Any

import httpx

from app.db.dragonfly import get_dragonfly

CACHE_SECONDS = 45
TIMEOUT = 2.5
USER_RE = re.compile(r"^[A-Za-z0-9_.\-]{1,64}$")
UA = "misa.lol (https://misa.lol; now-playing block)"
_inflight: set[str] = set()


def clean_user(value: Any) -> str:
    v = str(value or "").strip()
    return v if USER_RE.match(v) else ""


async def fetch_json(url: str) -> dict | None:
    """One GET, JSON or None. Split out so tests can stub the network."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, headers={"User-Agent": UA, "Accept": "application/json"}) as client:
            r = await client.get(url)
            if r.status_code != 200:
                return None
            return r.json()
    except (httpx.HTTPError, ValueError):
        return None


def _track(payload: dict | None) -> dict | None:
    """ListenBrainz's shape → {track, artist, at} or None."""
    try:
        listens = payload["payload"]["listens"]
        first = listens[0]
        meta = first["track_metadata"]
        track = str(meta.get("track_name") or "").strip()[:80]
        artist = str(meta.get("artist_name") or "").strip()[:80]
        if not track:
            return None
        return {"track": track, "artist": artist, "at": int(first.get("listened_at") or 0)}
    except (KeyError, IndexError, TypeError, AttributeError):
        return None


async def lookup(user: str) -> dict:
    """Ask ListenBrainz. Returns {playing: bool, track, artist, at, ok: bool}; ok False when nothing came back at all."""
    now = _track(await fetch_json(f"https://api.listenbrainz.org/1/user/{user}/playing-now"))
    if now:
        return {"ok": True, "playing": True, "track": now["track"], "artist": now["artist"], "at": int(time.time())}
    last = await fetch_json(f"https://api.listenbrainz.org/1/user/{user}/listens?count=1")
    if last is None:
        return {"ok": False, "playing": False, "track": "", "artist": "", "at": 0}
    t = _track(last)
    if not t:
        return {"ok": True, "playing": False, "track": "", "artist": "", "at": 0}
    return {"ok": True, "playing": False, "track": t["track"], "artist": t["artist"], "at": t["at"]}


async def refresh(user: str) -> dict | None:
    """Look the user up and cache it (a failed lookup is cached too, briefly, so a dead name isn't hammered)."""
    if user in _inflight:
        return None
    _inflight.add(user)
    try:
        data = await lookup(user)
        try:
            await get_dragonfly().set(f"np:{user}", json.dumps(data), ex=CACHE_SECONDS if data["ok"] else 20)
        except (RuntimeError, OSError):
            pass
        return data
    finally:
        _inflight.discard(user)


async def cached(user: str) -> dict | None:
    try:
        raw = await get_dragonfly().get(f"np:{user}")
    except (RuntimeError, OSError):
        return None
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except ValueError:
        return None


async def peek(user: str) -> dict | None:
    """For the page render: the cached answer, or None right now with a refresh started in the background."""
    data = await cached(user)
    if data is None and user not in _inflight:
        try:
            asyncio.get_running_loop().create_task(refresh(user))
        except RuntimeError:
            pass
    return data


async def get(user: str) -> dict | None:
    """For the API: the cached answer, or a fresh one (awaited)."""
    return await cached(user) or await refresh(user)


def ago(at: int, now: float | None = None) -> str:
    """'just now' / '4 min ago' / '2 h ago' / '3 d ago' — the page's wording for a last listen."""
    if not at:
        return ""
    d = max(0, int((now or time.time()) - at))
    if d < 90:
        return "just now"
    if d < 3600:
        return f"{d // 60} min ago"
    if d < 86400:
        return f"{d // 3600} h ago"
    return f"{d // 86400} d ago"
