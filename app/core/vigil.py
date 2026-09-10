"""The vigil (v3.134): a shelf of candles a page's visitors light, and that burn down on their own.

A candle is nothing but the fact that somebody was here and stopped for a second — no words, no name. It
stands at full height when it is lit and shrinks as its hours run out; when the last of them is gone it
snuffs itself and leaves the shelf. So the shelf is a picture of the last few hours of a page, and an
empty one means nobody has come by for a while. The owner picks how long a candle lasts (6, 12 or 24 hours).

Keys (per user id):
  vg:<uid>              a sorted set of the candles still lit, scored by the second each one goes out
  vg:<uid>:seen:<hash>  one candle per visitor per page per day (a salted hash, exactly like the guestbook's)
A member is "<id>|<lit>|<burn>" — a short random id, the second it was lit and how many seconds it burns for.
Nothing about who lit it is kept anywhere, not even in the member.
"""
from __future__ import annotations

import hashlib
import secrets
import time

from app.db.dragonfly import get_dragonfly

MAX = 48  # candles kept alight at once; the ones nearest going out are dropped first
SHOWN = 24  # candles the page draws
BURNS = {"6": 6 * 3600, "12": 12 * 3600, "24": 24 * 3600}
DEFAULT = "12"


def burn_of(value: object) -> int | None:
    """Seconds a candle burns for a given `settings.vigil`, or None when the vigil is off."""
    key = str(value or "").strip()
    return BURNS.get(key)


def visitor_key(user_id: str, addr: str, ua: str, salt: str) -> str:
    return f"vg:{user_id}:seen:" + hashlib.sha256(f"{salt}|{addr}|{ua}".encode()).hexdigest()[:24]


def _parse(member: str, now: int) -> dict[str, int | str] | None:
    bits = str(member).split("|")
    if len(bits) != 3 or not bits[0]:
        return None
    try:
        lit, burn = int(bits[1]), int(bits[2])
    except ValueError:
        return None
    if burn <= 0:
        return None
    left = lit + burn - now
    if left <= 0:
        return None
    return {"id": bits[0], "lit": lit, "burn": burn, "left": left}


async def light(user_id: str, burn: int, visitor: str) -> dict[str, int | str] | None:
    """Light one. Returns the candle, or None when this visitor lit one here today already."""
    r = get_dragonfly()
    if not await r.set(visitor, "1", nx=True, ex=24 * 3600):
        return None
    now = int(time.time())
    member = f"{secrets.token_urlsafe(6)}|{now}|{int(burn)}"
    key = f"vg:{user_id}"
    pipe = r.pipeline()
    pipe.zremrangebyscore(key, "-inf", now)
    pipe.zadd(key, {member: now + int(burn)})
    pipe.zremrangebyrank(key, 0, -(MAX + 1))  # keep the MAX with the most time left
    pipe.expire(key, max(BURNS.values()) + 3600)
    await pipe.execute()
    return _parse(member, now)


async def lit(user_id: str, limit: int = SHOWN) -> list[dict[str, int | str]]:
    """The candles still burning, oldest first — stubs on the left, freshly lit on the right."""
    now = int(time.time())
    try:
        members = await get_dragonfly().zrangebyscore(f"vg:{user_id}", now + 1, "+inf")
    except (RuntimeError, OSError):
        return []
    out = [c for c in (_parse(m, now) for m in members) if c]
    out.sort(key=lambda c: (c["lit"], str(c["id"])))
    return out[-limit:]


async def count(user_id: str) -> int:
    now = int(time.time())
    try:
        return int(await get_dragonfly().zcount(f"vg:{user_id}", now + 1, "+inf"))
    except (RuntimeError, OSError):
        return 0


async def snuff(user_id: str) -> None:
    """Clear the shelf. The owner's own button — visitors can't put anybody's candle out."""
    await get_dragonfly().delete(f"vg:{user_id}")


async def forget(user_id: str) -> None:
    await get_dragonfly().delete(f"vg:{user_id}")
