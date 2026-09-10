"""Milestone cards (v3.124): `GET /<username>/milestone.png?n=1000` — a 1200×630 card for a view count the page has really
crossed (100 · 1k · 10k · 100k · 1M). Anything the page hasn't reached is a 404, so the card can't lie for you. Drawn with the
same fonts and grain as the share card; cached five minutes per (page, milestone)."""
from __future__ import annotations

import io
import time
from datetime import datetime, timezone
from typing import Any

from PIL import Image, ImageDraw, ImageFilter

from app.share_card import ASH, CRIMSON, INK, MUTE, TEXT, _clean, _dagger, _font, _rgb

W, H = 1200, 630
MILESTONES = (100, 1000, 10000, 100000, 1000000)
LINES = {
    100: "a hundred people found this.",
    1000: "a thousand. it’s a place now.",
    10000: "ten thousand. you’re on the map.",
    100000: "a hundred thousand. be weird online again.",
    1000000: "a million. what.",
}
MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")
_cache: dict[tuple[str, int], tuple[float, bytes]] = {}
CACHE_TTL = 300.0
CACHE_MAX = 300


def reached(views: int) -> int | None:
    """The biggest milestone a view count has crossed, or None."""
    hit = [m for m in MILESTONES if views >= m]
    return hit[-1] if hit else None


def short(n: int) -> str:
    return f"{n // 1000}k" if 1000 <= n < 1000000 else "1M" if n >= 1000000 else str(n)


def render_milestone(config: dict[str, Any], n: int, now: datetime | None = None) -> bytes:
    profile = config.get("profile") or {}
    settings = config.get("settings") or {}
    username = "".join(c for c in str(profile.get("username") or "").lower() if c.isalnum() or c == "_")[:24] or "yourname"
    name = _clean(str(profile.get("displayName") or username), "Inter-ExtraBold.ttf")[:40] or username
    accent = _rgb(settings.get("accentColor"), CRIMSON)
    now = now or datetime.now(timezone.utc)

    img = Image.new("RGB", (W, H), INK)
    glow = Image.new("RGB", (W, H), INK)
    g = ImageDraw.Draw(glow)
    g.ellipse((-200, 120, 700, 900), fill=tuple(int(INK[i] + (accent[i] - INK[i]) * 0.42) for i in range(3)))
    g.ellipse((760, -300, 1500, 300), fill=tuple(int(INK[i] + (accent[i] - INK[i]) * 0.18) for i in range(3)))
    glow = glow.filter(ImageFilter.GaussianBlur(130))
    img.paste(glow)
    d = ImageDraw.Draw(img, "RGBA")
    for y in range(0, H, 3):
        d.line((0, y, W, y), fill=(255, 255, 255, 5))

    _dagger(d, 84, 74, 40, CRIMSON)
    d.text((118, 80), "misa.lol", font=_font("Inter-SemiBold.ttf", 28), fill=TEXT)
    d.text((84, 176), "milestone", font=_font("Inter-SemiBold.ttf", 22), fill=ASH)

    f_num = _font("Inter-ExtraBold.ttf", 200)
    num = f"{n:,}"
    l, t, r, b = d.textbbox((0, 0), num, font=f_num)
    d.text((76, 400 - b), num, font=f_num, fill=accent)  # the digits' baseline-ish bottom sits at 400 whatever the count
    d.text((84, 424), f"views on misa.lol/{username}", font=_font("Inter-Medium.ttf", 34), fill=TEXT)
    d.text((84, 478), LINES.get(n, "thanks for coming."), font=_font("Caveat-SemiBold.ttf", 46), fill=accent)
    d.text((84, 572), f"{name} · as of {now.day} {MONTHS[now.month - 1]} {now.year} · one page for links, music and socials", font=_font("Inter-Medium.ttf", 19), fill=MUTE)

    out = io.BytesIO()
    img.save(out, "PNG", optimize=True)
    return out.getvalue()


def cached_milestone(username: str, config: dict[str, Any], n: int) -> bytes:
    key = (username, n)
    t = time.monotonic()
    hit = _cache.get(key)
    if hit and hit[0] > t:
        return hit[1]
    png = render_milestone(config, n)
    if len(_cache) >= CACHE_MAX:
        for k, (exp, _) in list(_cache.items()):
            if exp <= t:
                _cache.pop(k, None)
        if len(_cache) >= CACHE_MAX:
            _cache.pop(next(iter(_cache)))
    _cache[key] = (t + CACHE_TTL, png)
    return png
