"""Neighbours (v3.144): pages that name each other, and only then.

You can name up to five other misa.lol pages. A name on your list does nothing on its own — it shows up on
your page only if that page names you back. So nobody ever appears beside anybody without both of them having
chosen it, which is the whole of the moderation story: there is nothing to report, because there is nothing
one person can put on another person's page.

Keys:
  nb:<uid>   the resolved mutual list as JSON, 10 minutes
Resolving costs one lookup per name, so it never happens while a page is being drawn: the render uses whatever
is cached (nothing, the first time) and the page asks for a fresh list itself, exactly like now-playing.
"""
from __future__ import annotations

import json
import re
from typing import Any

from app.db.dragonfly import get_dragonfly

MAX = 5
TTL = 600
_NAME = re.compile(r"^[a-z0-9_.-]{1,32}$")


def clean(raw: Any, mine: str = "") -> list[str]:
    """The names on a list: lowercased, tidied, deduped, at most MAX, never your own."""
    names: list[str] = []
    for value in (raw if isinstance(raw, list) else [])[:20]:
        name = str(value or "").strip().lower().lstrip("@").removeprefix("misa.lol/")
        if not _NAME.match(name) or name == str(mine or "").lower() or name in names:
            continue
        names.append(name)
        if len(names) == MAX:
            break
    return names


async def peek(user_id: str) -> list[dict[str, str]] | None:
    """The cached mutual list, or None when nothing has resolved it yet. Never touches the data API."""
    try:
        raw = await get_dragonfly().get(f"nb:{user_id}")
    except (RuntimeError, OSError):
        return None
    if not raw:
        return None
    try:
        out = json.loads(raw)
    except ValueError:
        return None
    return out if isinstance(out, list) else None


async def resolve(user_id: str, username: str, names: list[str], find_user, get_profile) -> list[dict[str, str]]:
    """Look each name up and keep the ones that name you back. Caches the answer for TTL."""
    mine = str(username or "").lower()
    out: list[dict[str, str]] = []
    for name in names:
        try:
            other = await find_user(username=name)
            if not other or getattr(other, "currently_suspended", False) or other.id == user_id:
                continue
            profile = await get_profile(other.id) or {}
        except Exception:
            continue
        theirs = clean((profile.get("settings") or {}).get("neighbours"), name)
        if mine and mine in theirs:
            p = profile.get("profile") or {}
            accent = str((profile.get("settings") or {}).get("accentColor") or "").strip()
            out.append({"username": name,
                        "name": str(p.get("displayName") or name)[:40],
                        "accent": accent if re.match(r"^#[0-9a-fA-F]{6}$", accent) else ""})
    try:
        await get_dragonfly().set(f"nb:{user_id}", json.dumps(out, separators=(",", ":")), ex=TTL)
    except (RuntimeError, OSError):
        pass
    return out


async def forget(user_id: str) -> None:
    await get_dragonfly().delete(f"nb:{user_id}")
