"""The guestbook (v3.117): visitors sign a page; the owner approves what shows. Kept in Dragonfly.

Keys (per user id):
  gb:<uid>:pending   list of JSON entries waiting for the owner   (newest first, at most 50)
  gb:<uid>:ok        list of JSON entries the owner approved      (newest first, at most 60)
  gb:<uid>:seen:<visitor>  one signature per visitor per page per day
An entry is {"id", "name", "line", "at"} — no addresses are stored; the visitor marker is a salted hash.
"""
from __future__ import annotations

import hashlib
import json
import re
import secrets
import time
from typing import Any

from app.db.dragonfly import get_dragonfly

PENDING_MAX = 50
APPROVED_MAX = 60
SHOWN_MAX = 24
NAME_MAX = 24
LINE_MAX = 120
_WS = re.compile(r"\s+")


def clean_name(value: Any) -> str:
    return _WS.sub(" ", str(value or "")).strip()[:NAME_MAX]


def clean_line(value: Any) -> str:
    return _WS.sub(" ", str(value or "")).strip()[:LINE_MAX]


def visitor_key(user_id: str, addr: str, ua: str, salt: str) -> str:
    return f"gb:{user_id}:seen:" + hashlib.sha256(f"{salt}|{addr}|{ua}".encode()).hexdigest()[:24]


async def sign(user_id: str, name: str, line: str, visitor: str) -> dict[str, Any] | None:
    """Queue a signature for the owner. Returns the entry, or None when this visitor already signed today."""
    r = get_dragonfly()
    if not await r.set(visitor, "1", nx=True, ex=24 * 3600):
        return None
    entry = {"id": secrets.token_urlsafe(9), "name": name, "line": line, "at": int(time.time())}
    key = f"gb:{user_id}:pending"
    pipe = r.pipeline()
    pipe.lpush(key, json.dumps(entry))
    pipe.ltrim(key, 0, PENDING_MAX - 1)
    await pipe.execute()
    return entry


async def _read(key: str, limit: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in await get_dragonfly().lrange(key, 0, limit - 1):
        try:
            e = json.loads(raw)
            if isinstance(e, dict) and e.get("id"):
                out.append(e)
        except ValueError:
            continue
    return out


async def approved(user_id: str, limit: int = SHOWN_MAX) -> list[dict[str, Any]]:
    try:
        return await _read(f"gb:{user_id}:ok", limit)
    except (RuntimeError, OSError):
        return []


async def pending(user_id: str) -> list[dict[str, Any]]:
    return await _read(f"gb:{user_id}:pending", PENDING_MAX)


async def _pop(key: str, entry_id: str) -> dict[str, Any] | None:
    r = get_dragonfly()
    for raw in await r.lrange(key, 0, -1):
        try:
            e = json.loads(raw)
        except ValueError:
            continue
        if isinstance(e, dict) and e.get("id") == entry_id:
            await r.lrem(key, 1, raw)
            return e
    return None


async def approve(user_id: str, entry_id: str) -> dict[str, Any] | None:
    """Move a pending entry to the approved list (newest first, capped)."""
    e = await _pop(f"gb:{user_id}:pending", entry_id)
    if e is None:
        return None
    key = f"gb:{user_id}:ok"
    r = get_dragonfly()
    pipe = r.pipeline()
    pipe.lpush(key, json.dumps(e))
    pipe.ltrim(key, 0, APPROVED_MAX - 1)
    await pipe.execute()
    return e


async def remove(user_id: str, entry_id: str) -> bool:
    """Bin an entry from either list."""
    return (await _pop(f"gb:{user_id}:pending", entry_id)) is not None or (await _pop(f"gb:{user_id}:ok", entry_id)) is not None


async def forget(user_id: str) -> None:
    r = get_dragonfly()
    await r.delete(f"gb:{user_id}:pending", f"gb:{user_id}:ok")
