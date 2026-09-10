"""Per-profile share cards (v3.8): misa.lol/<name>/card.png — 1200×630, drawn with Pillow from the saved config.

Same design as images/share.png: ink ground, the page's accent as a glow, the name in Inter 800 with the badge,
the handle, the bio, the † mark and a handwritten line. Nothing is fetched at render time — the avatar is the
initial letter on an accent disc (remote avatar URLs are untrusted and slow). Fonts ship in app/assets/fonts (OFL).
"""
from __future__ import annotations

import io
import re
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTS = Path(__file__).parent / "assets" / "fonts"
W, H = 1200, 630
INK = (5, 6, 6)
TEXT = (242, 242, 240)
ASH = (169, 166, 161)
MUTE = (128, 125, 120)
CRIMSON = (240, 6, 70)
GOLD = (230, 195, 107)
HEX_RE = re.compile(r"^#([0-9a-fA-F]{6})$")

_cache: dict[str, tuple[float, bytes]] = {}
CACHE_TTL = 300.0
CACHE_MAX = 500


@lru_cache(maxsize=32)
def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


@lru_cache(maxsize=8)
def _charset(name: str) -> frozenset[int]:
    """Code points the (latin-subset) font can draw — anything else would render as a box."""
    try:
        from fontTools.ttLib import TTFont  # optional; without it we keep ASCII + Latin-1 only
        return frozenset(TTFont(str(FONTS / name)).getBestCmap().keys())
    except Exception:
        return frozenset(range(0x20, 0x7F)) | frozenset(range(0xA0, 0x100))


def _clean(text: str, font_name: str) -> str:
    cs = _charset(font_name)
    return " ".join("".join(ch for ch in text if ord(ch) in cs or ch == " ").split())


def _dagger(d: ImageDraw.ImageDraw, x: int, y: int, h: int, fill: tuple[int, int, int]) -> None:
    """The † mark as vectors (the subset fonts don't carry U+2020)."""
    w = int(h * 0.62)
    bar = max(3, h // 9)
    cx = x + w // 2
    d.rectangle((cx - bar // 2, y, cx + bar // 2, y + int(h * 0.62)), fill=fill)
    d.polygon([(cx - bar // 2, y + int(h * 0.62)), (cx + bar // 2, y + int(h * 0.62)), (cx, y + h)], fill=fill)
    d.rectangle((x, y + int(h * 0.24), x + w, y + int(h * 0.24) + bar), fill=fill)


def _rgb(value: Any, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    m = HEX_RE.match(str(value or "").strip())
    if not m:
        return fallback
    h = m.group(1)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _fit(draw: ImageDraw.ImageDraw, text: str, font_name: str, size: int, max_width: int, min_size: int) -> ImageFont.FreeTypeFont:
    """Shrink a single line until it fits."""
    while size > min_size:
        font = _font(font_name, size)
        if draw.textlength(text, font=font) <= max_width:
            return font
        size -= 4
    return _font(font_name, min_size)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int, max_lines: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
            if len(lines) == max_lines:
                break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    if len(lines) == max_lines and (len(words) > sum(len(l.split()) for l in lines)):
        lines[-1] = lines[-1].rstrip(".,;:") + "…"
    return lines


def render_profile_card(config: dict[str, Any]) -> bytes:
    profile = config.get("profile") or {}
    settings = config.get("settings") or {}
    username = re.sub(r"[^a-z0-9_]", "", str(profile.get("username") or "").lower())[:24] or "yourname"
    name = _clean(str(profile.get("displayName") or username), "Inter-ExtraBold.ttf")[:40] or username
    bio = _clean(str(profile.get("description") or ""), "PlayfairDisplay-Italic.ttf")[:200]
    accent = _rgb(settings.get("accentColor"), CRIMSON)
    badge = next((b for b in (config.get("badges") or []) if isinstance(b, dict) and b.get("enabled", True) and b.get("owned", True)), None)
    # v3.115: the custom card — the owner's own handwritten line, and a style: glow (the default), poster (accent ground),
    # mono (ink, a hairline frame, no accent). Lifetime; the gate clears settings.shareCard below that.
    custom = settings.get("shareCard") if isinstance(settings.get("shareCard"), dict) else {}
    style = str(custom.get("style") or "glow").lower()
    if style not in ("glow", "poster", "mono"):
        style = "glow"
    tagline = _clean(str(custom.get("tagline") or ""), "Caveat-SemiBold.ttf")[:60]
    show_bio = custom.get("showBio", True) is not False
    lum = 0.2126 * accent[0] + 0.7152 * accent[1] + 0.0722 * accent[2]
    if style == "poster":
        ground, text, ash, mute, line_color, disc, disc_text = accent, (TEXT if lum < 150 else INK), (TEXT if lum < 150 else INK), (TEXT if lum < 150 else INK), (TEXT if lum < 150 else INK), (TEXT if lum < 150 else INK), accent
    elif style == "mono":
        ground, text, ash, mute, line_color, disc, disc_text = INK, TEXT, ASH, MUTE, TEXT, TEXT, INK
    else:
        ground, text, ash, mute, line_color, disc, disc_text = INK, TEXT, ASH, MUTE, accent, accent, TEXT

    img = Image.new("RGB", (W, H), ground)
    if style == "glow":
        # accent glow, blurred
        glow = Image.new("RGB", (W, H), INK)
        g = ImageDraw.Draw(glow)
        g.ellipse((640, 40, 1400, 760), fill=tuple(int(INK[i] + (accent[i] - INK[i]) * 0.42) for i in range(3)))
        g.ellipse((-260, -320, 360, 200), fill=tuple(int(INK[i] + (accent[i] - INK[i]) * 0.16) for i in range(3)))
        glow = glow.filter(ImageFilter.GaussianBlur(120))
        img.paste(glow)
    # scanline grain
    d = ImageDraw.Draw(img, "RGBA")
    for y in range(0, H, 3):
        d.line((0, y, W, y), fill=(255, 255, 255, 5) if style != "poster" else (0, 0, 0, 6))
    if style == "mono":
        d.rectangle((40, 40, W - 40, H - 40), outline=TEXT, width=2)

    # brand
    _dagger(d, 84, 74, 40, CRIMSON if style == "glow" else text)
    d.text((118, 80), "misa.lol", font=_font("Inter-SemiBold.ttf", 28), fill=text)

    # avatar disc with the initial
    cx, cy, r = 940, 250, 120
    d.ellipse((cx - r - 10, cy - r - 10, cx + r + 10, cy + r + 10), fill=(255, 255, 255, 18) if style != "poster" else (0, 0, 0, 20))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=disc)
    initial = (name[:1] or username[:1]).lower()
    f_init = _font("Inter-ExtraBold.ttf", 132)
    l, t, r2, b = d.textbbox((0, 0), initial, font=f_init)
    d.text((cx - (l + r2) / 2, cy - (t + b) / 2), initial, font=f_init, fill=disc_text)

    # name (+ badge), handle, bio
    f_name = _fit(d, name, "Inter-ExtraBold.ttf", 88, 640, 44)
    d.text((84, 176), name, font=f_name, fill=text)
    if badge:
        nw = d.textlength(name, font=f_name)
        bc = _rgb(badge.get("color"), (59, 130, 246)) if style == "glow" else text
        bx, by, br = 84 + nw + 34, 176 + f_name.size * 0.52, 22
        d.ellipse((bx - br, by - br, bx + br, by + br), fill=bc)
        tick = TEXT if style == "glow" else ground
        d.line((bx - 10, by + 1, bx - 3, by + 9), fill=tick, width=5)
        d.line((bx - 3, by + 9, bx + 11, by - 8), fill=tick, width=5)
    y = 176 + f_name.size + 22
    d.text((84, y), f"misa.lol/{username}", font=_font("Inter-Medium.ttf", 30), fill=ash)
    y += 62
    if bio and show_bio:
        f_bio = _font("PlayfairDisplay-Italic.ttf", 40)
        for line in _wrap(d, bio, f_bio, 640, 3):
            d.text((84, y), line, font=f_bio, fill=text)
            y += 52
    # handwritten line + footer — the owner's own line when they wrote one
    d.text((84, 512), tagline or "be weird online again.", font=_font("Caveat-SemiBold.ttf", 44), fill=line_color)
    if tagline:
        d.text((84, 576), f"misa.lol/{username} · one page for links, music and socials", font=_font("Inter-Medium.ttf", 19), fill=mute)
    else:
        d.text((84, 576), "one page for your links, music and socials · free forever · not a subscription", font=_font("Inter-Medium.ttf", 19), fill=mute)

    out = io.BytesIO()
    img.save(out, "PNG", optimize=True)
    return out.getvalue()


def cached_card(username: str, config: dict[str, Any]) -> bytes:
    now = time.monotonic()
    hit = _cache.get(username)
    if hit and hit[0] > now:
        return hit[1]
    png = render_profile_card(config)
    if len(_cache) >= CACHE_MAX:
        for k, (exp, _) in list(_cache.items()):
            if exp <= now:
                _cache.pop(k, None)
        if len(_cache) >= CACHE_MAX:
            _cache.pop(next(iter(_cache)))
    _cache[username] = (now + CACHE_TTL, png)
    return png


def forget_card(username: str) -> None:
    _cache.pop(username, None)
