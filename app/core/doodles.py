"""Visitor doodles (v3.123): a chalkboard on the page — visitors scribble, the owner keeps the ones they like. Dragonfly.

Keys (per user id):
  dd:<uid>:pending   list of JSON entries waiting for the owner   (newest first, at most 30)
  dd:<uid>:ok        list of JSON entries the owner approved      (newest first, at most 24)
  dd:<uid>:seen:<visitor>  one drawing per visitor per page per day (a salted hash, like the guestbook's — no address kept)
An entry is {"id", "s": [[x, y, x, y, …], …], "c": colour key, "at"}: strokes as flat integer point lists in a 200×140
space, at most 40 strokes / 400 points a stroke / 3,000 points in all — a few kilobytes at the very most.
"""
from __future__ import annotations

import json
import secrets
import time
from typing import Any

from app.db.dragonfly import get_dragonfly

PENDING_MAX = 30
APPROVED_MAX = 24
SHOWN_MAX = 12
W, H = 200, 140
STROKES_MAX = 40
POINTS_MAX = 400
TOTAL_MAX = 3000
COLOURS = {"chalk": "#EEE8E2", "accent": "var(--accent)", "pink": "#ff9ac4", "sky": "#7fd3ff", "gold": "#E6C36B"}


def clean(strokes: Any, colour: Any) -> tuple[list[list[int]], str] | None:
    """Validate a drawing. Returns (strokes, colour key) or None when there's nothing drawable in it."""
    key = str(colour or "chalk").lower()
    if key not in COLOURS:
        key = "chalk"
    if not isinstance(strokes, list):
        return None
    out: list[list[int]] = []
    total = 0
    for raw in strokes[:STROKES_MAX]:
        if not isinstance(raw, list):
            continue
        pts: list[int] = []
        flat = raw
        if raw and isinstance(raw[0], list):  # [[x, y], …] is welcome too
            flat = [v for p in raw if isinstance(p, list) and len(p) == 2 for v in p]
        for i in range(0, len(flat) - 1, 2):
            try:
                x, y = int(round(float(flat[i]))), int(round(float(flat[i + 1])))
            except (TypeError, ValueError):
                continue
            x, y = max(0, min(W, x)), max(0, min(H, y))
            if pts and abs(pts[-2] - x) < 1 and abs(pts[-1] - y) < 1:
                continue
            pts += [x, y]
            if len(pts) >= POINTS_MAX * 2:
                break
        if len(pts) >= 2:
            out.append(pts)
            total += len(pts) // 2
            if total >= TOTAL_MAX:
                break
    return (out, key) if out else None


def svg(entry: dict[str, Any], cls: str = "doodle") -> str:
    """An inline SVG for a drawing: one path per stroke, a dot for a single point."""
    colour = COLOURS.get(str(entry.get("c") or "chalk"), COLOURS["chalk"])
    paths = []
    for pts in entry.get("s") or []:
        if not isinstance(pts, list) or len(pts) < 2:
            continue
        try:
            nums = [int(v) for v in pts]
        except (TypeError, ValueError):
            continue
        if len(nums) == 2:
            paths.append(f'<circle cx="{nums[0]}" cy="{nums[1]}" r="2" fill="currentColor" stroke="none"/>')
            continue
        d = f"M{nums[0]} {nums[1]}" + "".join(f"L{nums[i]} {nums[i + 1]}" for i in range(2, len(nums) - 1, 2))
        paths.append(f'<path d="{d}"/>')
    # currentColor so the accent can be a CSS variable (presentation attributes can't hold var())
    return (
        f'<svg class="{cls}" viewBox="0 0 {W} {H}" role="img" aria-label="a visitor’s drawing" style="color:{colour}" fill="none" stroke="currentColor" '
        f'stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round">{"".join(paths)}</svg>'
    )


def visitor_key(user_id: str, visitor_hash: str) -> str:
    return f"dd:{user_id}:seen:{visitor_hash}"


async def draw(user_id: str, strokes: list[list[int]], colour: str, visitor: str) -> dict[str, Any] | None:
    """Queue a drawing for the owner. Returns the entry, or None when this visitor drew today already."""
    r = get_dragonfly()
    if not await r.set(visitor, "1", nx=True, ex=24 * 3600):
        return None
    entry = {"id": secrets.token_urlsafe(9), "s": strokes, "c": colour, "at": int(time.time())}
    key = f"dd:{user_id}:pending"
    pipe = r.pipeline()
    pipe.lpush(key, json.dumps(entry, separators=(",", ":")))
    pipe.ltrim(key, 0, PENDING_MAX - 1)
    await pipe.execute()
    return entry


async def _read(key: str, limit: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in await get_dragonfly().lrange(key, 0, limit - 1):
        try:
            e = json.loads(raw)
            if isinstance(e, dict) and e.get("id") and isinstance(e.get("s"), list):
                out.append(e)
        except ValueError:
            continue
    return out


async def approved(user_id: str, limit: int = SHOWN_MAX) -> list[dict[str, Any]]:
    try:
        return await _read(f"dd:{user_id}:ok", limit)
    except (RuntimeError, OSError):
        return []


async def pending(user_id: str) -> list[dict[str, Any]]:
    return await _read(f"dd:{user_id}:pending", PENDING_MAX)


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
    e = await _pop(f"dd:{user_id}:pending", entry_id)
    if e is None:
        return None
    key = f"dd:{user_id}:ok"
    pipe = get_dragonfly().pipeline()
    pipe.lpush(key, json.dumps(e, separators=(",", ":")))
    pipe.ltrim(key, 0, APPROVED_MAX - 1)
    await pipe.execute()
    return e


async def remove(user_id: str, entry_id: str) -> bool:
    return (await _pop(f"dd:{user_id}:pending", entry_id)) is not None or (await _pop(f"dd:{user_id}:ok", entry_id)) is not None


async def forget(user_id: str) -> None:
    await get_dragonfly().delete(f"dd:{user_id}:pending", f"dd:{user_id}:ok")
