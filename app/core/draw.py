"""The draw (v3.138): the page deals every visitor one line, and keeps dealing them the same one all day.

The owner writes a small deck — a line each, up to twelve. A visitor gets one of them, picked from the short
salted hash the view counter already has for them and the date in UTC, so it is theirs for the day and
somebody else standing next to them gets a different one. Nothing is stored: the pick is a pure function of
the deck, the visitor and the day, worked out fresh on every render.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

MAX = 12
LINE_MAX = 120
_WS = re.compile(r"[ \t]+")


def clean(raw: Any) -> list[str]:
    """The deck: one line a line, blanks dropped, at most MAX."""
    if isinstance(raw, list):
        lines = [str(v or "") for v in raw[:40]]
    else:
        lines = str(raw or "").replace("\r\n", "\n").split("\n")
    out: list[str] = []
    for line in lines:
        text = _WS.sub(" ", line).strip()[:LINE_MAX]
        if text:
            out.append(text)
        if len(out) == MAX:
            break
    return out


def today(now: datetime | None = None) -> str:
    return (now or datetime.now(timezone.utc)).strftime("%Y-%m-%d")


def pick(deck: list[str], seed: str, day: str | None = None) -> str:
    """One line for this visitor, this day. The same three arguments always give the same line."""
    if not deck:
        return ""
    if len(deck) == 1:
        return deck[0]
    digest = hashlib.sha256(f"{day or today()}|{seed}".encode()).digest()
    return deck[int.from_bytes(digest[:8], "big") % len(deck)]
