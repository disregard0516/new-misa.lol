"""The moon (v3.146): the real phase, tonight, drawn from arithmetic.

No network, no data, no cache: the moon is a clock everybody already shares, and its phase is a division. The
page draws the lit part as one SVG path — the terminator is an ellipse, so the lit region is a semicircle
joined to an ellipse arc, which is exact rather than an approximation of a picture of the moon.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone

SYNODIC = 29.530588853                  # days, mean synodic month
KNOWN_NEW = 2451550.1                   # julian day of the new moon of 6 january 2000
NAMES = (  # the named phases are moments; each gets the day or so around it, the rest is the long slopes
    (0.03, "new moon"), (0.22, "waxing crescent"), (0.28, "first quarter"), (0.47, "waxing gibbous"),
    (0.53, "full moon"), (0.72, "waning gibbous"), (0.78, "last quarter"), (0.97, "waning crescent"),
    (1.01, "new moon"),
)


def age(now: datetime | None = None) -> float:
    """How far through the cycle we are, 0 (new) to 1 (just before new again)."""
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    julian = now.timestamp() / 86400.0 + 2440587.5
    return ((julian - KNOWN_NEW) / SYNODIC) % 1.0


def phase(now: datetime | None = None) -> tuple[float, float, str, bool]:
    """(where in the cycle, how much of it is lit, what it's called, is it waxing)."""
    where = age(now)
    lit = (1 - math.cos(2 * math.pi * where)) / 2
    name = next(n for edge, n in NAMES if where < edge)
    return where, lit, name, where < 0.5


def svg(now: datetime | None = None, size: int = 26) -> tuple[str, str]:
    """(the drawing, what it's called) — the lit part as one path, so a crescent really is a crescent."""
    where, lit, name, waxing = phase(now)
    r = size / 2
    cx = cy = r
    if lit < 0.005:
        body = f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r - 0.6:.2f}" class="moon__dark"/>'
    elif lit > 0.995:
        body = f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r - 0.6:.2f}" class="moon__lit"/>'
    else:
        rr = r - 0.6
        rx = abs(math.cos(2 * math.pi * where)) * rr          # the terminator, seen edge-on
        outer = 1 if waxing else 0                            # the lit limb: right while waxing, left while waning
        inner = outer if lit > 0.5 else 1 - outer             # the terminator bows away once past half
        body = (f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{rr:.2f}" class="moon__dark"/>'
                f'<path class="moon__lit" d="M{cx:.2f} {cy - rr:.2f} A{rr:.2f} {rr:.2f} 0 0 {outer} {cx:.2f} {cy + rr:.2f} '
                f'A{rx:.2f} {rr:.2f} 0 0 {inner} {cx:.2f} {cy - rr:.2f} Z"/>')
    pct = round(lit * 100)
    label = f"{name}, {pct}% lit" if 0 < pct < 100 else name
    return (f'<svg class="moon" viewBox="0 0 {size} {size}" width="{size}" height="{size}" role="img" '
            f'aria-label="tonight\u2019s moon: {label}">{body}</svg>'), label
