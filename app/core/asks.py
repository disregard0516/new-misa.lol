"""The ask box (v3.128): visitors leave a question; the owner answers it, and the answer lands on the page.

The guestbook is a wall people sign. This one talks back — a page with the box on says *ask me anything*, and
every answered question shows up underneath, question and answer together. A question nobody answers is
never public: it sits in the owner's dashboard until they answer it or bin it.

Keys (per user id):
  ak:<uid>:new           questions waiting for an answer          (newest first, at most NEW_MAX)
  ak:<uid>:done          answered ones, what the page shows       (newest answer first, at most DONE_MAX)
  ak:<uid>:seen:<hash>   one question per visitor per page per day
An entry is {"id", "q", "at"} and, once answered, {"a", "at_a"} as well. Nothing about who asked is kept —
the daily marker is a salted hash, exactly like the guestbook's.
"""
from __future__ import annotations

import hashlib
import json
import re
import secrets
import time
from typing import Any

from app.db.dragonfly import get_dragonfly

NEW_MAX = 40
DONE_MAX = 30
SHOWN_MAX = 8
Q_MAX = 180
A_MAX = 400
_WS = re.compile(r"\s+")


def clean_question(value: Any) -> str:
    return _WS.sub(" ", str(value or "")).strip()[:Q_MAX]


def clean_answer(value: Any) -> str:
    return _WS.sub(" ", str(value or "")).strip()[:A_MAX]


def visitor_key(user_id: str, addr: str, ua: str, salt: str) -> str:
    return f"ak:{user_id}:seen:" + hashlib.sha256(f"{salt}|{addr}|{ua}".encode()).hexdigest()[:24]


async def ask(user_id: str, question: str, visitor: str) -> dict[str, Any] | None:
    """Queue a question. None when this visitor already asked this page today."""
    r = get_dragonfly()
    if not await r.set(visitor, "1", nx=True, ex=24 * 3600):
        return None
    entry = {"id": secrets.token_urlsafe(9), "q": question, "at": int(time.time())}
    key = f"ak:{user_id}:new"
    pipe = r.pipeline()
    pipe.lpush(key, json.dumps(entry))
    pipe.ltrim(key, 0, NEW_MAX - 1)
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


async def waiting(user_id: str) -> list[dict[str, Any]]:
    try:
        return await _read(f"ak:{user_id}:new", NEW_MAX)
    except (RuntimeError, OSError):
        return []


async def answered(user_id: str, limit: int = SHOWN_MAX) -> list[dict[str, Any]]:
    """What the page shows: answered questions, newest answer first."""
    try:
        return await _read(f"ak:{user_id}:done", limit)
    except (RuntimeError, OSError):
        return []


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


async def answer(user_id: str, entry_id: str, text: str) -> dict[str, Any] | None:
    """Answer a waiting question — that, and only that, puts it on the page."""
    text = clean_answer(text)
    if not text:
        return None
    e = await _pop(f"ak:{user_id}:new", entry_id)
    if e is None:
        return None
    e["a"] = text
    e["at_a"] = int(time.time())
    key = f"ak:{user_id}:done"
    r = get_dragonfly()
    pipe = r.pipeline()
    pipe.lpush(key, json.dumps(e))
    pipe.ltrim(key, 0, DONE_MAX - 1)
    await pipe.execute()
    return e


async def edit(user_id: str, entry_id: str, text: str) -> dict[str, Any] | None:
    """Change an answer that is already up — it keeps its place in the list."""
    text = clean_answer(text)
    if not text:
        return None
    r = get_dragonfly()
    key = f"ak:{user_id}:done"
    raws = await r.lrange(key, 0, -1)
    for i, raw in enumerate(raws):
        try:
            e = json.loads(raw)
        except ValueError:
            continue
        if isinstance(e, dict) and e.get("id") == entry_id:
            e["a"] = text
            await r.lset(key, i, json.dumps(e))
            return e
    return None


async def remove(user_id: str, entry_id: str) -> bool:
    """Bin a question, answered or not."""
    return (await _pop(f"ak:{user_id}:new", entry_id)) is not None or (await _pop(f"ak:{user_id}:done", entry_id)) is not None


async def forget(user_id: str) -> None:
    r = get_dragonfly()
    await r.delete(f"ak:{user_id}:new", f"ak:{user_id}:done")
