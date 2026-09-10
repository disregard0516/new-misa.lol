"""The archive (v3.143): a page keeps what it used to be.

Every save puts the page it just replaced on a shelf. The owner can look at the shelf, see the page as it was
on any of those days and put it back; and if they want to, they can let visitors look too — a page you can
read backwards. It is also the thing that catches you: *I broke my page at 3am* stops being a disaster.

Keys (per user id):
  ar:<uid>   a list of snapshots, newest first, at most MAX, the whole list expiring after a year
A snapshot is {"at": epoch, "cfg": the whole profile config as it was}. Nothing about visitors is in it; it is
the owner's own page, exactly as they saved it, and account deletion drops the list with everything else.
"""
from __future__ import annotations

import json
import time
from typing import Any

from app.db.dragonfly import get_dragonfly

MAX = 12                    # snapshots kept
TTL = 365 * 24 * 3600
SIZE_MAX = 256 * 1024       # a page config that won't fit in a quarter-megabyte isn't a page config


def _dump(config: Any) -> str | None:
    try:
        raw = json.dumps(config, separators=(",", ":"), default=str)
    except (TypeError, ValueError):
        return None
    return raw if 0 < len(raw) <= SIZE_MAX else None


async def keep(user_id: str, config: Any, now: int | None = None) -> bool:
    """Shelve this version of the page. False when there was nothing new to keep."""
    raw = _dump(config)
    if raw is None:
        return False
    r = get_dragonfly()
    key = f"ar:{user_id}"
    try:
        newest = await r.lindex(key, 0)
    except (RuntimeError, OSError):
        return False
    when = int(now or time.time())
    if newest:
        try:
            top = json.loads(newest)
            if top.get("cfg") == config:
                return False                            # saved twice without changing anything
            if isinstance(top.get("at"), int) and when <= top["at"]:
                when = top["at"] + 1                    # two saves in one second still get their own moment
        except ValueError:
            pass
    entry = json.dumps({"at": when, "cfg": json.loads(raw)}, separators=(",", ":"))
    pipe = r.pipeline()
    pipe.lpush(key, entry)
    pipe.ltrim(key, 0, MAX - 1)
    pipe.expire(key, TTL)
    await pipe.execute()
    return True


async def _all(user_id: str) -> list[dict[str, Any]]:
    try:
        rows = await get_dragonfly().lrange(f"ar:{user_id}", 0, MAX - 1)
    except (RuntimeError, OSError):
        return []
    out = []
    for row in rows:
        try:
            e = json.loads(row)
        except ValueError:
            continue
        if isinstance(e, dict) and isinstance(e.get("at"), int) and isinstance(e.get("cfg"), dict):
            out.append(e)
    return out


async def shelf(user_id: str) -> list[int]:
    """Just the days, newest first — the bodies stay on the server until something asks for one."""
    return [e["at"] for e in await _all(user_id)]


async def at(user_id: str, when: int) -> dict[str, Any] | None:
    """The page as it was at that exact moment, or None if that snapshot has fallen off the shelf."""
    for e in await _all(user_id):
        if e["at"] == int(when):
            return e["cfg"]
    return None


async def forget(user_id: str) -> None:
    await get_dragonfly().delete(f"ar:{user_id}")
