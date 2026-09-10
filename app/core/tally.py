"""The tally (v3.136): the page asks the visitor something, and everyone sees how it went.

The ask box is questions coming in. This is one going out: the owner sets a question and two to four answers,
and every visitor picks one. The count is scratched on the card as tally marks — four strokes and a slash
through them, the way you'd count days on a wall — so a page with three answers looks like three little
scratched groups, not a chart.

Keys (per user id, and per question):
  tl:<uid>:<qid>            a hash of choice index -> count            (90 days, pushed out on every vote)
  tl:<uid>:<qid>:seen:<h>   one vote per visitor per question          (the same salted hash as the guestbook)
`qid` is a short digest of the question and its answers, so rewording either starts a clean count and lets
everybody answer the new one. Nothing about who voted is kept — only how many picked each answer.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

from app.db.dragonfly import get_dragonfly

Q_MAX = 120
OPT_MAX = 40
OPTS_MIN, OPTS_MAX = 2, 4
TTL = 90 * 24 * 3600
MARKS_MAX = 25  # tally marks drawn before the number carries the rest
_WS = re.compile(r"\s+")


def clean(raw: Any) -> tuple[str, list[str], str] | None:
    """Validate settings.tally. Returns (question, answers, qid), or None when there is no question to ask."""
    if not isinstance(raw, dict):
        return None
    question = _WS.sub(" ", str(raw.get("q") or "")).strip()[:Q_MAX]
    seen: list[str] = []
    for value in (raw.get("options") if isinstance(raw.get("options"), list) else [])[:12]:
        option = _WS.sub(" ", str(value or "")).strip()[:OPT_MAX]
        if option and option.lower() not in [s.lower() for s in seen]:
            seen.append(option)          # blanks and repeats are skipped rather than spent
            if len(seen) == OPTS_MAX:
                break
    if not question or len(seen) < OPTS_MIN:
        return None
    qid = hashlib.sha256(("|".join([question] + seen)).encode()).hexdigest()[:10]
    return question, seen, qid


def visitor_key(user_id: str, qid: str, addr: str, ua: str, salt: str) -> str:
    return f"tl:{user_id}:{qid}:seen:" + hashlib.sha256(f"{salt}|{addr}|{ua}".encode()).hexdigest()[:24]


async def counts(user_id: str, qid: str, options: int) -> list[int]:
    """How many picked each answer, in the answers' own order. Unreadable or empty reads as all zeroes."""
    try:
        raw = await get_dragonfly().hgetall(f"tl:{user_id}:{qid}")
    except (RuntimeError, OSError):
        return [0] * options
    out = []
    for i in range(options):
        try:
            out.append(max(0, int(raw.get(str(i), raw.get(str(i).encode(), 0)) or 0)))
        except (TypeError, ValueError):
            out.append(0)
    return out


async def vote(user_id: str, qid: str, choice: int, options: int, visitor: str) -> list[int] | None:
    """Count one answer. Returns the new counts, or None when this visitor has answered this question already."""
    if not 0 <= choice < options:
        return None
    r = get_dragonfly()
    if not await r.set(visitor, "1", nx=True, ex=TTL):
        return None
    key = f"tl:{user_id}:{qid}"
    pipe = r.pipeline()
    pipe.hincrby(key, str(choice), 1)
    pipe.expire(key, TTL)
    await pipe.execute()
    return await counts(user_id, qid, options)


def marks(n: int) -> str:
    """One count as tally marks: groups of five, four uprights and a slash through them."""
    drawn = min(max(0, int(n)), MARKS_MAX)
    groups = []
    while drawn > 0:
        five = min(5, drawn)
        drawn -= five
        strokes = "".join('<i></i>' for _ in range(min(4, five)))
        groups.append(f'<b class="mark{" mark--five" if five == 5 else ""}">{strokes}</b>')
    return "".join(groups)


async def forget(user_id: str) -> None:
    """Every question this page has ever asked."""
    r = get_dragonfly()
    keys = [k async for k in r.scan_iter(match=f"tl:{user_id}:*", count=200)]
    if keys:
        await r.delete(*keys)
