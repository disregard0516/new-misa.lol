"""The visitor's-eye replay (v3.127): the last visits to a page, as little stories the owner can read.

Counts already say *how many*. This says *what happened*: someone arrived from tiktok on a phone, tapped
“new single” twelve seconds later, signed the guestbook, left. The owner turns it on with `settings.replay`
(free, off by default); with it off nothing is written at all.

What is kept, per user, in one Dragonfly list `rp:<uid>` (newest first, at most MAX events, whole list
expires after a week):

    t  unix seconds
    v  the first 8 characters of the same salted visitor hash the view counter dedupes on — enough to tell
       one visit from another for half an hour, and short enough that it is not an identifier
    k  what happened: in · tap · sign · draw · ask
    d  a detail: the referrer host for `in` (empty for a direct visit), the link id for `tap`, nothing else
    m  1 when the visit came from a phone-shaped browser (from the user agent, which is not itself kept)

No addresses, no user agents, no names, no reading of anything the visitor typed. `visits()` groups the
events into visits (same short hash, within GAP) and hands back the newest ones.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any

from app.db.dragonfly import get_dragonfly

MAX = 120          # events kept per page — about ten to thirty visits
TTL = 7 * 24 * 3600
GAP = 1800         # events this far apart are different visits (same window the view counter dedupes on)
KINDS = ("in", "tap", "sign", "draw", "ask", "light")
MOBILE_RE = re.compile(r"iphone|android|ipad|mobile|silk|kindle", re.I)
_HOST_RE = re.compile(r"^[a-z0-9.\-]{1,80}$")


def phone_like(user_agent: str) -> bool:
    return bool(MOBILE_RE.search(user_agent or ""))


def clean_detail(kind: str, detail: Any) -> str:
    d = str(detail or "")[:80]
    if kind == "in":
        d = d.lower()
        return d if _HOST_RE.match(d) else ""
    return re.sub(r"[^A-Za-z0-9_-]", "", d)[:64]


async def note(user_id: str, kind: str, visitor: str, detail: Any = "", *, phone: bool = False) -> None:
    """Write one event. Best effort: the replay never gets in the way of a page."""
    if kind not in KINDS or not user_id or not visitor:
        return
    ev = {"t": int(time.time()), "v": str(visitor)[:8], "k": kind, "d": clean_detail(kind, detail)}
    if phone:
        ev["m"] = 1
    try:
        r = get_dragonfly()
        key = f"rp:{user_id}"
        pipe = r.pipeline()
        pipe.lpush(key, json.dumps(ev, separators=(",", ":")))
        pipe.ltrim(key, 0, MAX - 1)
        pipe.expire(key, TTL)
        await pipe.execute()
    except (RuntimeError, OSError, TypeError, ValueError):
        pass


async def events(user_id: str) -> list[dict]:
    """Every event kept for a page, oldest first — the list itself is newest first, so it comes back reversed."""
    try:
        raw = await get_dragonfly().lrange(f"rp:{user_id}", 0, MAX - 1)
    except (RuntimeError, OSError):
        return []
    raw = list(reversed(raw or []))
    out: list[dict] = []
    for item in raw or []:
        try:
            ev = json.loads(item)
        except (TypeError, ValueError):
            continue
        if isinstance(ev, dict) and ev.get("k") in KINDS and isinstance(ev.get("t"), int):
            out.append(ev)
    return out


async def visits(user_id: str, limit: int = 10) -> list[dict]:
    """The newest visits, each one a little story: when it started, where from, on what, and what happened in order."""
    evs = sorted(await events(user_id), key=lambda e: e["t"])  # a stable sort, so events inside one second keep the order they happened in
    groups: list[dict] = []
    for ev in evs:
        g = groups[-1] if groups else None
        if g and g["v"] == ev.get("v", "") and ev["t"] - g["end"] <= GAP:
            g["end"] = ev["t"]
        else:
            g = {"v": ev.get("v", ""), "at": ev["t"], "end": ev["t"], "phone": False, "from": "", "events": []}
            groups.append(g)
        if ev.get("m"):
            g["phone"] = True
        if ev["k"] == "in" and ev.get("d") and not g["from"]:
            g["from"] = ev["d"]
        g["events"].append({"k": ev["k"], "d": ev.get("d", ""), "after": max(0, ev["t"] - g["at"])})
    out = []
    for g in groups[-limit:][::-1]:                     # newest visit first
        taps = [e["d"] for e in g["events"] if e["k"] == "tap" and e["d"]]
        out.append({
            "at": g["at"], "seconds": g["end"] - g["at"], "from": g["from"] or None,
            "device": "phone" if g["phone"] else "desktop",
            "events": g["events"], "taps": taps,
        })
    return out


async def forget(user_id: str) -> None:
    try:
        await get_dragonfly().delete(f"rp:{user_id}")
    except (RuntimeError, OSError):
        pass
