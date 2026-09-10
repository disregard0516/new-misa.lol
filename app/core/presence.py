"""Live presence (v3.118): “3 people here right now”. Kept in Dragonfly.

Key (per user id):
  pr:<uid>   sorted set — member: the salted visitor hash (the same one analytics uses, no address kept),
             score: the second of their last heartbeat. Trimmed to the window on every read; the key expires on its own.
A page beats on load and every 30 s while its tab is visible, and sends a leave beacon when it goes; anyone quiet for
WINDOW seconds stops counting. The number is never exact and never needs to be.
"""
from __future__ import annotations

import time

from app.db.dragonfly import get_dragonfly

WINDOW = 75  # seconds a visitor counts after their last heartbeat (the page beats every 30 s)


async def beat(user_id: str, visitor: str) -> int:
    """Mark this visitor as here; return how many are here now (this one included)."""
    r = get_dragonfly()
    now = time.time()
    key = f"pr:{user_id}"
    pipe = r.pipeline()
    pipe.zadd(key, {visitor: now})
    pipe.zremrangebyscore(key, "-inf", now - WINDOW)
    pipe.zcard(key)
    pipe.expire(key, WINDOW * 2)
    res = await pipe.execute()
    return int(res[2] or 0)


async def leave(user_id: str, visitor: str) -> None:
    await get_dragonfly().zrem(f"pr:{user_id}", visitor)


async def here(user_id: str) -> int:
    """How many are here now, without counting the caller."""
    r = get_dragonfly()
    key = f"pr:{user_id}"
    pipe = r.pipeline()
    pipe.zremrangebyscore(key, "-inf", time.time() - WINDOW)
    pipe.zcard(key)
    res = await pipe.execute()
    return int(res[1] or 0)


async def forget(user_id: str) -> None:
    await get_dragonfly().delete(f"pr:{user_id}")
