"""Public profile page (misa.lol/<username>) — the v2 design system applied to a real profile config.

Renders one self-contained HTML document from the ProfileConfig the dashboard saves
(profile / settings / assets / socials / badges). Every value coming from the config is
escaped or validated before it touches the markup or the stylesheet.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from functools import lru_cache
from html import escape
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
URL_RE = re.compile(r"^(?:https?://|/)[^\s\"'<>]+$", re.I)

FONTS = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,400;1,400&display=swap"

# platform → sprite icon (a handful of neutral glyphs; brand logos are deliberately not drawn)
PLATFORM_ICON = {
    "youtube": "video", "tiktok": "video", "twitch": "video", "kick": "video",
    "spotify": "music", "soundcloud": "music",
    "discord": "users", "telegram": "send", "reddit": "users",
    "github": "code",
    "steam": "game", "roblox": "game",
    "email": "mail",
    "instagram": "image", "pinterest": "image", "snapchat": "image",
    "paypal": "bag", "patreon": "heart", "bitcoin": "coin", "ethereum": "coin", "litecoin": "coin", "solana": "coin",
    "x": "globe", "threads": "globe", "facebook": "globe", "linkedin": "globe",
    "custom url": "link",
}

# v3.112: the built-in Supporter cursors — gold on a dark outline so they read on any page; 24px, hotspot at the centre
def _cursor_svg(body: str) -> str:
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">{body}</svg>'
    return "data:image/svg+xml," + svg.replace("#", "%23").replace('"', "'").replace("<", "%3C").replace(">", "%3E")


BUILTIN_CURSORS = {
    "star": _cursor_svg('<path d="M12 2l2.6 6.9L22 12l-7.4 3.1L12 22l-2.6-6.9L2 12l7.4-3.1z" fill="#E6C36B" stroke="#1a1408" stroke-width="1.4" stroke-linejoin="round"/>'),
    "ring": _cursor_svg('<circle cx="12" cy="12" r="8" fill="none" stroke="#E6C36B" stroke-width="3"/><circle cx="12" cy="12" r="8" fill="none" stroke="#1a1408" stroke-width="1" opacity=".6"/><circle cx="12" cy="12" r="1.6" fill="#E6C36B"/>'),
    "snow": _cursor_svg('<g fill="none" stroke="#E6C36B" stroke-width="2" stroke-linecap="round"><path d="M12 2v20M2 12h20M4.9 4.9l14.2 14.2M19.1 4.9L4.9 19.1"/><path d="M12 2l-2.5 2.5M12 2l2.5 2.5M12 22l-2.5-2.5M12 22l2.5-2.5M2 12l2.5-2.5M2 12l2.5 2.5M22 12l-2.5-2.5M22 12l-2.5 2.5"/></g>'),
}

# v3.114: the page fonts — a curated set loaded from Google Fonts only when chosen (key → family, css stack, size scale)
PAGE_FONTS = {
    "inter": ("", "'Inter',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif", 1.0),
    "playfair": ("Playfair+Display:ital,wght@0,400;0,700;1,400", "'Playfair Display',Georgia,serif", 1.06),
    "cormorant": ("Cormorant+Garamond:ital,wght@0,500;0,700;1,500", "'Cormorant Garamond',Georgia,serif", 1.12),
    "space-mono": ("Space+Mono:wght@400;700", "'Space Mono',ui-monospace,Menlo,Consolas,monospace", 0.94),
    "caveat": ("Caveat:wght@500;700", "'Caveat','Segoe Print',cursive", 1.22),
    "vt323": ("VT323", "'VT323',ui-monospace,monospace", 1.24),
    "bebas": ("Bebas+Neue", "'Bebas Neue',Impact,sans-serif", 1.08),
    "unifraktur": ("UnifrakturMaguntia", "'UnifrakturMaguntia','Old English Text MT',serif", 1.06),
}
SUPPORTER_FONTS = {"unifraktur", "cormorant"}  # the exclusive two
PLAYER_STYLES = ("bars", "minimal", "vinyl")

SPRITE = (
    '<svg width="0" height="0" style="position:absolute" aria-hidden="true">'
    '<symbol id="i-link" viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></symbol>'
    '<symbol id="i-music" viewBox="0 0 24 24"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></symbol>'
    '<symbol id="i-video" viewBox="0 0 24 24"><rect x="2" y="6" width="14" height="12" rx="2"/><path d="m16 10 6-3v10l-6-3z"/></symbol>'
    '<symbol id="i-users" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></symbol>'
    '<symbol id="i-send" viewBox="0 0 24 24"><path d="m22 2-7 20-4-9-9-4z"/><path d="M22 2 11 13"/></symbol>'
    '<symbol id="i-code" viewBox="0 0 24 24"><path d="m16 18 6-6-6-6M8 6l-6 6 6 6"/></symbol>'
    '<symbol id="i-game" viewBox="0 0 24 24"><path d="M6 12h4M8 10v4M15 13h.01M18 11h.01"/><path d="M17.3 5H6.7a4 4 0 0 0-3.96 3.44L2 15.5A2.5 2.5 0 0 0 4.5 18c.8 0 1.5-.4 2-1l1.5-2h8l1.5 2c.5.6 1.2 1 2 1a2.5 2.5 0 0 0 2.5-2.5l-.74-7.06A4 4 0 0 0 17.3 5z"/></symbol>'
    '<symbol id="i-mail" viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></symbol>'
    '<symbol id="i-image" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></symbol>'
    '<symbol id="i-bag" viewBox="0 0 24 24"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><path d="M3 6h18M16 10a4 4 0 0 1-8 0"/></symbol>'
    '<symbol id="i-heart" viewBox="0 0 24 24"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></symbol>'
    '<symbol id="i-coin" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v10M9.5 9.5h3.5a1.75 1.75 0 0 1 0 3.5H9.5h4a1.75 1.75 0 0 1 0 3.5H9.5"/></symbol>'
    '<symbol id="i-globe" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/></symbol>'
    '<symbol id="i-pin" viewBox="0 0 24 24"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/></symbol>'
    '<symbol id="i-eye" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></symbol>'
    '<symbol id="i-check" viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></symbol>'
    '<symbol id="i-play" viewBox="0 0 24 24"><path fill="currentColor" stroke="none" d="M8 5v14l11-7z"/></symbol>'
    '<symbol id="i-pause" viewBox="0 0 24 24"><path fill="currentColor" stroke="none" d="M6 5h4v14H6zM14 5h4v14h-4z"/></symbol>'
    '<symbol id="i-arrow" viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></symbol>'
    # v3.125: the weather block's sky
    '<symbol id="i-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></symbol>'
    '<symbol id="i-moon" viewBox="0 0 24 24"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></symbol>'
    '<symbol id="i-cloud" viewBox="0 0 24 24"><path d="M17.5 19H7a4.5 4.5 0 0 1-.6-8.96A6 6 0 0 1 18 9.5a4.75 4.75 0 0 1-.5 9.5z"/></symbol>'
    '<symbol id="i-cloud-sun" viewBox="0 0 24 24"><path d="M12 2v2M4.2 5.2l1.4 1.4M2 12h2"/><path d="M8 9.6A4 4 0 0 1 14.7 8"/><path d="M18 20H9a4 4 0 0 1-.5-7.97A5 5 0 0 1 18 12a4 4 0 0 1 0 8z"/></symbol>'
    '<symbol id="i-fog" viewBox="0 0 24 24"><path d="M4 9h12M6 13h14M4 17h10"/></symbol>'
    '<symbol id="i-rain" viewBox="0 0 24 24"><path d="M17.5 15H7a4.5 4.5 0 0 1-.6-8.96A6 6 0 0 1 18 5.5a4.75 4.75 0 0 1-.5 9.5z"/><path d="M8 18v3M12 18v3M16 18v3"/></symbol>'
    '<symbol id="i-snow" viewBox="0 0 24 24"><path d="M17.5 14H7a4.5 4.5 0 0 1-.6-8.96A6 6 0 0 1 18 4.5a4.75 4.75 0 0 1-.5 9.5z"/><path d="M8 18h.01M12 20h.01M16 18h.01M10 21h.01M14 22h.01"/></symbol>'
    '<symbol id="i-storm" viewBox="0 0 24 24"><path d="M17.5 13H7a4.5 4.5 0 0 1-.6-8.96A6 6 0 0 1 18 3.5a4.75 4.75 0 0 1-.5 9.5z"/><path d="m13 12-3 5h4l-3 5"/></symbol>'
    "</svg>"
)


def _color(value, default: str) -> str:
    value = str(value or "").strip()
    return value if HEX_RE.match(value) else default


def _url(value) -> str:
    value = str(value or "").strip()
    return value if URL_RE.match(value) else ""


def _num(value, default: float, lo: float, hi: float) -> float:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, n))


def _hex_rgb(color: str) -> str:
    """#rgb / #rrggbb → 'r,g,b' for rgba() mixing (falls back to ink)."""
    c = color.lstrip("#")
    if len(c) in (3, 4):
        c = "".join(ch * 2 for ch in c[:3])
    c = c[:6]
    try:
        return f"{int(c[0:2], 16)},{int(c[2:4], 16)},{int(c[4:6], 16)}"
    except ValueError:
        return "5,6,6"


_TZ_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_+\-]*(/[A-Za-z0-9_+\-]+){0,2}$")


@lru_cache(maxsize=256)
def _zone(name: str) -> ZoneInfo | None:
    """v3.118: an IANA zone for the clock block, or None for anything that isn't one."""
    if not name or len(name) > 64 or not _TZ_RE.match(name):
        return None
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, OSError):
        return None


def _clock(zone: ZoneInfo) -> tuple[str, str]:
    """(“3:12 am” with a blinking colon, the ISO time) for a zone, right now."""
    now = datetime.now(zone)
    hour = now.hour % 12 or 12
    text = f'{hour}<span class="blk__colon">:</span>{now.minute:02d} {"am" if now.hour < 12 else "pm"}'
    return text, now.strftime("%Y-%m-%dT%H:%M%z")


_WORD_RE = re.compile(r"[^a-z0-9]")


def _secret(raw) -> tuple[str, str, str, int] | None:
    """v3.119: (verifier, ciphertext hex, label, word length) for settings.secret — the word and the link stay out of
    the page source: the browser hashes what the visitor types, and the link is XORed with a keystream from the word."""
    if not isinstance(raw, dict):
        return None
    word = _WORD_RE.sub("", str(raw.get("word") or "").lower())[:24]
    url = _url(raw.get("url"))
    if len(word) < 3 or not url:
        return None
    label = escape(str(raw.get("label") or "").strip()[:40]) or "you found it"
    key = hashlib.sha256(word.encode()).digest()
    verifier = hashlib.sha256(b"misa-secret|" + word.encode()).hexdigest()
    plain = url.encode()[:512]
    stream = b"".join(hashlib.sha256(key + bytes([i])).digest() for i in range(len(plain) // 32 + 1))
    cipher = bytes(a ^ b for a, b in zip(plain, stream)).hex()
    return verifier, cipher, label, len(word)


_CAPSULE_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def _capsule(raw, now: datetime | None = None) -> tuple[bool, str, str, str] | None:
    """v3.129: (opened, the date as a word, the ISO instant, the message) for settings.capsule.

    A sealed capsule's message never reaches the browser — the server decides, by the clock, whether to send
    the words at all. Until then the page shows only the date it opens and a countdown to it.
    """
    if not isinstance(raw, dict):
        return None
    text = re.sub(r"\s+", " ", str(raw.get("text") or "")).strip()[:600]
    m = _CAPSULE_DATE.match(str(raw.get("at") or "").strip())
    if not text or not m:
        return None
    try:
        when = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=timezone.utc)
    except ValueError:
        return None
    now = now or datetime.now(timezone.utc)
    word = f"{when.day} {MONTHS[when.month - 1]} {when.year}"
    return when <= now, word, when.strftime("%Y-%m-%dT00:00:00Z"), text


def _night(raw, now: datetime | None = None) -> tuple[bool, str] | None:
    """v3.142: the night shift — (is it night there now, the hour as a word) for settings.night.

    A page can have parts that only exist after dark where its owner is. The window is the *owner's* clock,
    not the visitor's, and the server decides: outside it the night blocks are never rendered at all, so their
    words are not in the page for anyone to read early.
    """
    if not isinstance(raw, dict):
        return None
    zone = _zone(str(raw.get("tz") or "").strip())
    if zone is None:
        return None
    try:
        start, end = int(raw.get("from", 23)), int(raw.get("to", 5))
    except (TypeError, ValueError):
        return None
    if not (0 <= start <= 23 and 0 <= end <= 23) or start == end:
        return None
    there = (now or datetime.now(timezone.utc)).astimezone(zone)
    hour = there.hour
    dark = start <= hour < end if start < end else (hour >= start or hour < end)
    return dark, there.strftime("%I:%M %p").lstrip("0").lower()


def _reverse(raw) -> tuple[str, list[str]] | None:
    """v3.135: (the title, the paragraphs) for settings.reverse — the writing on the back of a page.

    A page can have a back: a second face the card turns over to show. This is the handwritten part of it;
    blocks with place "back" go there too, so the back can exist with no writing at all.
    """
    if not isinstance(raw, dict):
        return None
    title = re.sub(r"\s+", " ", str(raw.get("title") or "")).strip()[:40]
    body = str(raw.get("text") or "").replace("\r\n", "\n").strip()[:800]
    paras = [re.sub(r"[ \t]+", " ", line).strip() for line in body.split("\n")]
    paras = [line for line in paras if line]
    if not title and not paras:
        return None
    return title or "the other side", paras


def _ic(name: str) -> str:
    return f'<svg class="ic" aria-hidden="true"><use href="#i-{name}"/></svg>'


MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")


def _age(since: str | None, now: datetime | None = None) -> tuple[int, str] | None:
    """v3.124: (days here, the footer's wording) from an account's created_at, or None when it can't be read."""
    if not since:
        return None
    raw = str(since).strip().replace("Z", "+00:00")
    try:
        start = datetime.fromisoformat(raw)
    except ValueError:
        try:
            start = datetime.fromisoformat(raw[:10])
        except ValueError:
            return None
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    now = now or datetime.now(timezone.utc)
    days = max(0, (now - start).days)
    label = "today" if days == 0 else f"{start.day} {MONTHS[start.month - 1]}" if days < 30 else f"{MONTHS[start.month - 1]} {start.year}"
    return days, label


def render_public_profile(config: dict, views: int | None = None, signatures: list | None = None, here: int | None = None, live: dict | None = None, drawings: list | None = None, since: str | None = None, weather: dict | None = None, asked: list | None = None, sky: str | None = None, candles: list | None = None, drawn: str | None = None, was_at: int | None = None, neighbours: list | None = None) -> str:
    profile = config.get("profile") or {}
    settings = config.get("settings") or {}
    assets = config.get("assets") or {}

    username = escape(str(profile.get("username") or "user"))
    display_name = escape(str(profile.get("displayName") or profile.get("username") or "user"))
    description = escape(str(profile.get("description") or ""))
    location = escape(str(profile.get("location") or ""))
    views = int(_num(views if views is not None else profile.get("views"), 0, 0, 10**12))

    accent = _color(settings.get("accentColor"), "#F00646")
    text = _color(settings.get("textColor"), "#F2F2F0")
    bg = _color(settings.get("backgroundColor"), "#050606")
    icon_color = _color(settings.get("iconColor"), accent)
    card_opacity = _num(settings.get("profileOpacity"), 0.72, 0, 1)
    bg_opacity = _num(settings.get("backgroundOpacity"), 0.55, 0, 1)
    blur = int(_num(settings.get("profileBlur"), 16, 0, 40))
    radius = int(_num(settings.get("profileRadius"), 28, 0, 60))
    gradient_border = bool(settings.get("profileGradient", True))
    show_views = bool(settings.get("showViews", True))
    show_badges = bool(settings.get("showBadges", True))
    show_socials = bool(settings.get("showSocials", True))
    entry_screen = bool(settings.get("entryScreen", False))
    entry_text = escape(str(settings.get("entryText") or "click to enter"))
    bg_effect = str(settings.get("backgroundEffect") or "None").lower()
    name_effect = str(settings.get("usernameEffect") or "None").lower()
    glow_name = bool(settings.get("usernameGlow", False))
    glow_social = bool(settings.get("socialGlow", False))
    # v3.112: the Lifetime set the pages promised — typewriter bio, an entrance animation, the footer badge off — and the
    # built-in Supporter cursors (star / ring / snow)
    typewriter = bool(settings.get("bioTypewriter", False))
    enter_anim = str(settings.get("entryAnimation") or "None").lower()
    if enter_anim not in ("fade", "rise", "flicker", "glitch"):
        enter_anim = ""
    hide_brand = bool(settings.get("hideBrand", False))
    builtin_cursor = str(settings.get("cursor") or "default").lower()
    if builtin_cursor not in BUILTIN_CURSORS:
        builtin_cursor = "default"
    # v3.113: the Supporter set — a tag by the name, gold sparks that trail the pointer, a gold border that turns
    guestbook_on = bool(settings.get("guestbook", False))  # v3.117: the guestbook — a scrapbook of signatures + a form
    asks_on = bool(settings.get("asks", False))            # v3.128: the ask box — questions in, answers out on the page
    doodles_on = bool(settings.get("doodles", False))  # v3.123: the chalkboard — visitors draw, the owner keeps what they like
    age = _age(since) if settings.get("since") else None  # v3.124: a page that ages — here since, a wax seal, a patina
    # v3.118: live presence (“3 people here right now”), the hit counter's style, and the clock block (in the blocks loop)
    presence_on = bool(settings.get("presence", False))
    mood_on = bool(settings.get("mood", False))  # v3.119: the background wash follows the visitor's hour
    secret = _secret(settings.get("secret"))
    capsule = _capsule(settings.get("capsule"))            # v3.129: the time capsule — sealed words the server holds back
    sky_city = re.sub(r"\s+", " ", str(settings.get("sky") or "")).strip()[:64]   # v3.130: the real weather, drawn over the page
    remember_on = bool(settings.get("remember", False))    # v3.132: the page remembers a returning visitor — in their browser, never here
    moon_on = bool(settings.get("moon", False))         # v3.146: tonight's real moon, drawn from arithmetic
    from app.core.neighbours import clean as _nb_clean
    neighbour_names = _nb_clean(settings.get("neighbours"), str(profile.get("username") or ""))   # v3.144
    night = _night(settings.get("night"))               # v3.142: the night shift — the owner's clock decides
    from app.core.draw import clean as _draw_clean, pick as _draw_pick
    deck = _draw_clean(settings.get("draw"))            # v3.138: the draw — one line a visitor, the same one all day
    from app.core.tally import clean as _tally_clean
    tally = _tally_clean(settings.get("tally"))         # v3.136: the tally — the page asks, and everyone sees the count
    reverse = _reverse(settings.get("reverse"))          # v3.135: the page has a back — writing, and any block placed there
    from app.core.vigil import burn_of as _burn_of
    vigil_burn = _burn_of(settings.get("vigil"))          # v3.134: the vigil — candles visitors light, that burn themselves out
    counter_style = str(settings.get("counterStyle") or "plain").lower()
    if counter_style not in ("odometer", "lcd", "flip"):
        counter_style = "plain"
    page_font = str(settings.get("font") or "inter").lower()
    if page_font not in PAGE_FONTS:
        page_font = "inter"
    font_query, font_stack, font_scale = PAGE_FONTS[page_font]
    fonts_href = (
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family="
        + ("Playfair+Display:ital,wght@0,400;0,700;0,800;1,400" if page_font == "playfair" else "Playfair+Display:ital,wght@0,400;1,400")
        + (f"&family={font_query}" if font_query and page_font != "playfair" else "")
        + ("&family=Caveat:wght@600" if (guestbook_on or doodles_on or settings.get("vigil")) and page_font != "caveat" else "")
        + "&display=swap"
    )
    player_style = str(settings.get("playerStyle") or "bars").lower()
    if player_style not in PLAYER_STYLES:
        player_style = "bars"
    blocks_raw = settings.get("blocks") if isinstance(settings.get("blocks"), list) else []
    # v3.116: link styles, avatar frames, four more living backgrounds (below), a tab title that moves
    link_style = str(settings.get("linkStyle") or "pill").lower()
    if link_style not in ("pill", "outline", "ghost", "brutal", "glass"):
        link_style = "pill"
    avatar_frame = str(settings.get("avatarFrame") or "none").lower()
    if avatar_frame not in ("ring", "halo", "pixel", "petals"):
        avatar_frame = ""
    tab_title = str(settings.get("tabTitle") or "none").lower()
    if tab_title not in ("breathe", "scroll", "blink"):
        tab_title = ""
    supporter_tag = bool(settings.get("supporterTag", False))
    sparkle_trail = bool(settings.get("sparkleTrail", False))
    gold_border = bool(settings.get("goldBorder", False))

    avatar = _url((assets.get("avatar") or {}).get("url"))
    bg_image = _url((assets.get("background") or {}).get("url"))
    bg_video = _url((assets.get("backgroundVideo") or {}).get("url"))
    audio = _url((assets.get("audio") or {}).get("url"))
    audio_name = escape(str((assets.get("audio") or {}).get("name") or "now playing"))
    audio_enabled = bool(assets.get("audioEnabled", True)) and bool(audio)
    volume = _num(assets.get("volume"), 0.6, 0, 1)
    cursor = _url((assets.get("cursor") or {}).get("url"))

    # ── pieces ──
    avatar_tag = (
        f'<img class="avatar" src="{escape(avatar, quote=True)}" alt="" width="96" height="96">'
        if avatar else f'<div class="avatar avatar--letter" aria-hidden="true">{escape(display_name[:1].lower() or "†")}</div>'
    )
    if avatar_frame:
        avatar_tag = f'<div class="avatar-wrap frame--{avatar_frame}">{avatar_tag}</div>'

    badge_tags = []
    if show_badges:
        for badge in config.get("badges") or []:
            if not (badge.get("enabled") and badge.get("owned")):
                continue
            name = escape(str(badge.get("name") or "").strip())
            if not name:
                continue
            color = _color(badge.get("color"), accent)
            badge_tags.append(f'<span class="badge" style="--b:{color}" title="{name}">{_ic("check")}<span>{name}</span></span>')
    badges = f'<div class="badges">{"".join(badge_tags)}</div>' if badge_tags else ""

    social_tags = []
    if show_socials:
        for social in config.get("socials") or []:
            if not social.get("enabled"):
                continue
            platform = str(social.get("platform") or "").strip()
            label = escape(str(social.get("label") or platform or "Link"))
            value = str(social.get("value") or "").strip()
            if not value:
                continue
            icon = PLATFORM_ICON.get(platform.lower(), "link")
            if social.get("displayMode") == "text":
                social_tags.append(f'<span class="link link--text">{_ic(icon)}<span class="link__label">{label}</span> <span class="link__value">{escape(value)}</span></span>')
                continue
            if platform.lower() == "email" and "@" in value and not value.startswith("mailto:"):
                href = "mailto:" + value
            elif value.startswith(("http://", "https://", "mailto:")):
                href = value
            else:
                href = "https://" + value
            sid = escape(re.sub(r"[^A-Za-z0-9_-]", "", str(social.get("id") or ""))[:64], quote=True)
            social_tags.append(
                f'<a class="link" href="{escape(href, quote=True)}" target="_blank" rel="noreferrer noopener"{f" data-go={chr(34)}{sid}{chr(34)}" if sid else ""}>{_ic(icon)}<span class="link__label">{label}</span><span class="sr-only"> (opens in a new tab)</span>{_ic("arrow")}</a>'
            )
    socials = f'<div class="links links--{link_style}">{"".join(social_tags)}</div>' if social_tags else ""

    # v3.115: content blocks — a heading, a paragraph, a quote, a divider, a “currently:” status — above or below the links
    top_blocks, bottom_blocks, back_blocks = [], [], []
    for blk in blocks_raw[:12]:
        if not isinstance(blk, dict) or blk.get("enabled") is False:
            continue
        if blk.get("night") and not (night and night[0]):
            continue                                    # v3.142: by day, a night block's words are not in the page at all
        kind = str(blk.get("type") or "").lower()
        blk_text = escape(str(blk.get("text") or "").strip()[:400])
        if kind == "divider":
            tag = '<hr class="blk blk--hr" aria-hidden="true">'
        elif kind == "weather":  # v3.125: “raining in berlin, 11°” — Open-Meteo through the server, never on the render's clock
            from app.core.weather import clean_place, line as wx_line
            place = clean_place(blk.get("city"))
            if not place:
                continue
            unit = "f" if str(blk.get("unit") or "c").lower() == "f" else "c"
            data = (weather or {}).get(place)
            if isinstance(data, dict) and "code" in data:
                words, deg, icon = wx_line(data, unit, str(blk.get("text") or "").strip()[:40])
                tag = f'<p class="blk blk--wx" data-wx>{_ic(icon)}<span class="blk__wx" data-wx-line>{escape(words)}</span><b class="blk__deg" data-wx-temp>{deg}</b></p>'
            else:
                tag = f'<p class="blk blk--wx" data-wx hidden>{_ic("cloud")}<span class="blk__wx" data-wx-line></span><b class="blk__deg" data-wx-temp></b></p>'
        elif kind == "nowplaying":  # v3.122: what the owner is listening to — typed, or live from ListenBrainz
            lb = str(blk.get("lb") or "").strip()
            if not re.match(r"^[A-Za-z0-9_.\-]{1,64}$", lb):
                lb = ""
            url = _url(blk.get("url"))
            data = (live or {}).get(lb) if lb else None
            label, line, is_live, at = "now playing", blk_text[:160], False, 0
            if isinstance(data, dict) and data.get("track"):
                line = escape(str(data["track"]) + (f' — {data["artist"]}' if data.get("artist") else ""))
                if data.get("playing"):
                    is_live = True
                else:
                    label, at = "last played", int(data.get("at") or 0)
            if not line and not lb:
                continue
            if label == "last played" and at:
                from app.core.nowplaying import ago as _ago
                label = f"last played · {_ago(at)}"
            inner = f'<a class="np__t" data-np-t href="{escape(url, quote=True)}" target="_blank" rel="noreferrer noopener">{line}</a>' if url and line else f'<span class="np__t" data-np-t>{line}</span>'
            tag = (
                f'<p class="blk blk--np{" is-live" if is_live else ""}"{f" data-np={chr(34)}{escape(lb, quote=True)}{chr(34)}" if lb else ""}{" hidden" if not line else ""}>'
                f'<span class="np__disc" aria-hidden="true"></span><span class="np__k" data-np-k>{label}</span>{inner}'
                f'<span class="np__bars" aria-hidden="true"><i></i><i></i><i></i></span></p>'
            )
        elif kind == "clock":  # v3.118: “it's 3:12 am in berlin” — the owner's hour, live
            tz_name = str(blk.get("tz") or "").strip()
            zone = _zone(tz_name)
            if zone is None:
                continue
            label = blk_text[:40] or escape(tz_name.rsplit("/", 1)[-1].replace("_", " ").lower())
            when, iso = _clock(zone)
            tag = f'<p class="blk blk--clock"><span class="blk__k">it’s</span> <time class="blk__time" datetime="{iso}" data-clock="{escape(tz_name, quote=True)}">{when}</time> <span class="blk__k">in {label}</span></p>'
        elif not blk_text:
            continue
        elif kind == "heading":
            tag = f'<h2 class="blk blk--h">{blk_text}</h2>'
        elif kind == "text":
            tag = f'<p class="blk blk--p">{blk_text}</p>'
        elif kind == "quote":
            tag = f'<blockquote class="blk blk--q">{blk_text}</blockquote>'
        elif kind == "status":
            tag = f'<p class="blk blk--now"><span class="blk__dot" aria-hidden="true"></span><span class="blk__k">currently</span> {blk_text}</p>'
        else:
            continue
        place = str(blk.get("place") or "").lower()
        # v3.135: a third destination — the back of the page
        (back_blocks if place == "back" else top_blocks if place == "top" else bottom_blocks).append(tag)
    blocks_top = f'<div class="blocks">{"".join(top_blocks)}</div>' if top_blocks else ""
    blocks_bottom = f'<div class="blocks">{"".join(bottom_blocks)}</div>' if bottom_blocks else ""

    guestbook_tag = ""
    if guestbook_on:
        slips = []
        for n, sig in enumerate(signatures or []):
            if not isinstance(sig, dict):
                continue
            who = escape(str(sig.get("name") or "").strip()[:24])
            line = escape(str(sig.get("line") or "").strip()[:120])
            if not who or not line:
                continue
            slips.append(f'<li class="slip" data-at="{int(sig.get("at") or 0)}" style="--r:{(n % 5 - 2) * 1.6:.1f}deg"><span class="slip__line">{line}</span><span class="slip__who">— {who}</span></li>')
        guestbook_tag = (
            '<section class="book" aria-labelledby="book-title">'
            '<h2 class="book__title" id="book-title">guestbook</h2>'
            + (f'<ul class="slips">{"".join(slips)}</ul>' if slips else '<p class="book__empty">nobody has signed yet. be the first.</p>')
            + '<button class="book__open" type="button" data-book-open aria-expanded="false" aria-controls="book-form">sign it</button>'
            f'<form class="book__form" id="book-form" data-book-form hidden>'
            '<label class="book__lab">your name<input name="name" maxlength="24" required autocomplete="nickname" placeholder="who are you"></label>'
            '<label class="book__lab">one line<input name="line" maxlength="120" required placeholder="say something, keep it weird"></label>'
            '<div class="book__row"><button type="submit">leave it</button><button type="button" data-book-close>never mind</button></div>'
            '<p class="book__msg" data-book-msg role="status"></p>'
            '</form></section>'
        )

    asks_tag = ""
    if asks_on:
        qa = []
        for e in (asked or [])[:8]:
            if not isinstance(e, dict):
                continue
            q = escape(str(e.get("q") or "").strip()[:180])
            a = escape(str(e.get("a") or "").strip()[:400])
            if not q or not a:
                continue
            qa.append(f'<li class="qa" data-at="{int(e.get("at_a") or e.get("at") or 0)}"><p class="qa__q">{q}</p><p class="qa__a">{a}</p></li>')
        asks_tag = (
            '<section class="asks" aria-labelledby="asks-title">'
            '<h2 class="asks__title" id="asks-title">ask me anything</h2>'
            '<form class="asks__form" data-ask-form>'
            '<label class="asks__lab"><span class="sr-only">your question</span>'
            '<input name="question" maxlength="180" required autocomplete="off" placeholder="ask me anything"></label>'
            '<button type="submit">send it</button>'
            '<p class="asks__msg" data-ask-msg role="status"></p>'
            '</form>'
            + (f'<ul class="qas">{"".join(qa)}</ul>' if qa else '<p class="asks__empty">no answers up yet — yours could be the first.</p>')
            + '</section>'
        )

    vigil_tag = ""
    if vigil_burn:
        sticks = []
        for c in (candles or [])[-24:]:
            if not isinstance(c, dict):
                continue
            try:
                left, burn = int(c.get("left") or 0), int(c.get("burn") or vigil_burn)
            except (TypeError, ValueError):
                continue
            if left <= 0 or burn <= 0:
                continue
            h = max(0.0, min(1.0, left / burn))
            sticks.append(
                f'<li class="candle" data-left="{left}" data-burn="{burn}" style="--h:{h:.3f}">'
                '<i class="candle__flame" aria-hidden="true"></i><b class="candle__wax"></b><u class="candle__pool"></u></li>'
            )
        hours = vigil_burn // 3600
        n = len(sticks)
        note = f'{n} candle{"" if n == 1 else "s"} burning · they go out after {hours} hours'
        vigil_tag = (
            '<section class="vigil" aria-labelledby="vigil-title">'
            '<h2 class="vigil__title" id="vigil-title">light a candle</h2>'
            + (f'<ul class="shelf" data-shelf>{"".join(sticks)}</ul><p class="vigil__note" data-vigil-note>{note}</p>'
               if sticks else
               f'<ul class="shelf" data-shelf></ul><p class="vigil__empty" data-vigil-note>the shelf is dark. nobody has lit one in {hours} hours.</p>')
            + f'<button class="vigil__light" type="button" data-vigil-light>light one</button>'
            '<p class="vigil__msg" data-vigil-msg role="status"></p>'
            '</section>'
        )

    board_tag = ""
    if doodles_on:
        from app.core.doodles import COLOURS, svg as doodle_svg
        tiles = []
        for n, e in enumerate(drawings or []):
            if isinstance(e, dict) and isinstance(e.get("s"), list):
                tiles.append(f'<li class="tile" data-at="{int(e.get("at") or 0)}" style="--r:{(n % 4 - 1.5) * .8:.1f}deg">{doodle_svg(e)}</li>')
        chalks = "".join(
            f'<label class="board__chalk" title="{name}"><input type="radio" name="colour" value="{key}"{" checked" if key == "chalk" else ""}><i style="--c:{val}" aria-hidden="true"></i><span class="sr-only">{name}</span></label>'
            for key, val, name in (("chalk", COLOURS["chalk"], "white chalk"), ("accent", COLOURS["accent"], "the page’s accent"), ("pink", COLOURS["pink"], "pink"), ("sky", COLOURS["sky"], "sky blue"), ("gold", COLOURS["gold"], "gold"))
        )
        board_tag = (
            '<section class="board" aria-labelledby="board-title">'
            '<h2 class="board__title" id="board-title">chalkboard</h2>'
            + (f'<ul class="wall">{"".join(tiles)}</ul>' if tiles else '<p class="board__empty">nobody has drawn yet. the chalk’s right there.</p>')
            + '<button class="board__open" type="button" data-board-open aria-expanded="false" aria-controls="board-form">draw something</button>'
            '<form class="board__form" id="board-form" data-board-form hidden>'
            '<canvas class="board__canvas" width="400" height="280" data-board-canvas tabindex="0" aria-label="a small chalkboard — draw with a finger or the mouse"></canvas>'
            f'<div class="board__palette" role="radiogroup" aria-label="chalk colour">{chalks}</div>'
            '<div class="board__row"><button type="submit">leave it</button><button type="button" data-board-clear>wipe</button><button type="button" data-board-close>never mind</button></div>'
            '<p class="board__msg" data-board-msg role="status"></p>'
            '</form></section>'
        )

    moon_tag = ""
    if moon_on:
        from app.core.moon import phase as _moon_phase, svg as _moon_svg
        _where, _lit, _mname, _wax = _moon_phase()
        _draw, _label = _moon_svg()
        moon_tag = (f'<span class="moonw{" moonw--full" if _lit > .96 else ""}" style="--lit:{_lit:.3f}" '
                    f'title="tonight\u2019s moon: {escape(_label)}">{_draw}</span>')

    nb_tag = ""
    if neighbour_names:
        rows = "".join(
            f'<li class="nb__one"><a href="/{escape(n["username"])}"'
            + (f' style="--nb:{escape(n["accent"])}"' if n.get("accent") else "")
            + f'><span class="nb__dot" aria-hidden="true"></span>{escape(str(n.get("name") or n["username"])[:40])}'
              f'<small>misa.lol/{escape(n["username"])}</small></a></li>'
            for n in (neighbours or []) if isinstance(n, dict) and n.get("username"))
        nb_tag = (
            '<section class="nb" aria-labelledby="nb-title" data-neighbours>'
            '<h2 class="nb__title" id="nb-title">neighbours</h2>'
            f'<ul class="nb__list" data-nb-list>{rows}</ul>'
            + ("" if rows else '<p class="nb__empty" data-nb-empty>nobody has named this page back yet.</p>')
            + '</section>'
        )

    was_tag = ""
    if was_at:
        when = datetime.fromtimestamp(int(was_at), timezone.utc)
        word = f"{when.day} {MONTHS[when.month - 1]} {when.year}"
        was_tag = (f'<p class="wasat" role="status">you\u2019re reading this page as it was on <b>{escape(word)}</b>. '
                   f'<a href="/{username}">back to now</a></p>')

    night_tag = ""
    if night and night[0] and any(isinstance(b, dict) and b.get("night") and b.get("enabled") is not False for b in blocks_raw[:12]):
        night_tag = (f'<p class="nightfall">it\u2019s {escape(night[1])} where {display_name} is. '
                     'some of this is only here now.</p>')

    draw_tag = ""
    if deck:
        line = drawn if isinstance(drawn, str) and drawn.strip() else _draw_pick(deck, "someone")
        draw_tag = (
            '<section class="draw" aria-labelledby="draw-title">'
            '<h2 class="draw__title" id="draw-title">for you, today</h2>'
            f'<p class="draw__card">{escape(line)}</p>'
            '</section>'
        )

    tally_tag = ""
    if tally:
        question, options, qid = tally
        rows = "".join(
            f'<li class="tal__row" data-tal-row="{i}">'
            f'<button class="tal__pick" type="button" data-tal-pick="{i}">{escape(opt)}</button>'
            f'<span class="tal__marks" data-tal-marks="{i}" aria-hidden="true"></span>'
            f'<span class="tal__n" data-tal-n="{i}"></span></li>'
            for i, opt in enumerate(options)
        )
        tally_tag = (
            f'<section class="tal" aria-labelledby="tal-title" data-tally="{escape(qid)}">'
            f'<h2 class="tal__title" id="tal-title">{escape(question)}</h2>'
            f'<ul class="tal__list">{rows}</ul>'
            '<p class="tal__msg" data-tal-msg role="status"></p>'
            '</section>'
        )

    # v3.135: the back of the page — a second face the card turns over to show
    flip_open = flip_close = back_tag = dogear_tag = ""
    if reverse or back_blocks:
        title, paras = reverse if reverse else ("the other side", [])
        note = "".join(f'<p class="back__p">{escape(line)}</p>' for line in paras)
        blocks_back = f'<div class="blocks">{"".join(back_blocks)}</div>' if back_blocks else ""
        flip_open = '<div class="flip" data-flip>'
        flip_close = "</div>"
        dogear_tag = ('<button class="dogear" type="button" data-flip-to="back" aria-expanded="false" aria-controls="card-back">'
                      '<span class="sr-only">turn the page over</span></button>'
                      '<span class="dogear__hint" aria-hidden="true">turn it over</span>')
        back_tag = (
            f'<section class="card card--back" id="card-back" data-card-back aria-label="the back of misa.lol/{username}">'
            f'<h2 class="back__title">{escape(title)}</h2>'
            f'{note}{blocks_back}'
            '<button class="dogear dogear--back" type="button" data-flip-to="front">'
            '<span class="sr-only">turn it back</span></button>'
            '<span class="dogear__hint" aria-hidden="true">turn it back</span>'
            '</section>'
        )

    location_tag = f'<p class="location">{_ic("pin")}{location}</p>' if location else ""
    fresh_tag, seal_tag, patina_tag, since_tag, age_class = "", "", "", "", ""
    if age:
        days, label = age
        since_tag = f'<span class="since">here since {label}</span>'
        if days < 7:
            fresh_tag, age_class = '<span class="fresh">new here</span>', " age-new"
        elif days >= 365:
            years = days // 365
            seal_tag = f'<span class="seal seal--gold" aria-hidden="true" title="here since {label}">†<b>{years}y</b></span>'
            patina_tag, age_class = '<i class="patina" aria-hidden="true"></i>', " age-year"
        elif days >= 30:
            seal_tag, age_class = f'<span class="seal" aria-hidden="true" title="here since {label}">†</span>', " age-month"
    if description and typewriter:
        # the full text stays in the document for screen readers and no-script; the visible copy types itself out
        description_tag = f'<p class="bio bio--type" data-type="{description}"><span class="sr-only">{description}</span><span class="bio__typed" aria-hidden="true"></span><span class="bio__caret" aria-hidden="true"></span></p>'
    else:
        description_tag = f'<p class="bio">{description}</p>' if description else ""
    views_tag = f'<span class="views">{_ic("eye")}{views:,} views</span>' if show_views and counter_style == "plain" else ""
    counter_tag = ""
    if show_views and counter_style != "plain":  # v3.118: a retro hit counter above the footer — each digit rolls up on load
        digits = str(views).rjust(6, "0")
        cells = "".join(
            f'<span class="odo__d"><span class="odo__col" style="--n:{d};--i:{i}">' + "".join(f"<i>{k}</i>" for k in range(10)) + "</span></span>"
            for i, d in enumerate(digits)
        )
        counter_tag = f'<div class="odo odo--{counter_style}" data-odo role="img" aria-label="{views:,} views"><span class="odo__label">you are visitor no.</span><span class="odo__digits" aria-hidden="true">{cells}</span></div>'
    secret_tag = ""
    if secret:
        v, c, lab, n = secret
        secret_tag = f'<div class="secret" data-secret data-v="{v}" data-c="{c}" data-n="{n}" hidden><p class="secret__k">†&nbsp;you said the word</p><a class="link" href="#" data-secret-link target="_blank" rel="noreferrer noopener">{_ic("link")}<span class="link__label">{lab}</span><span class="sr-only"> (opens in a new tab)</span>{_ic("arrow")}</a></div><form class="secret__ask" data-secret-ask hidden><label class="sr-only" for="secret-word">say the word</label><input id="secret-word" autocomplete="off" autocapitalize="none" spellcheck="false" placeholder="say the word"></form>'
    again_tag = ""
    if remember_on:
        # the line is written by the browser from its own localStorage; the server sends an empty shell and nothing else
        again_tag = ('<p class="again" data-again hidden title="your own browser remembers this. '
                     'misa.lol is not told, and clearing your site data forgets it."></p>')

    sky_tag = ""
    if sky_city:
        # what the sky is doing right now where the owner is — the server sends the first state, the page's poll keeps it current
        state = str(sky or "").strip().lower()
        state = state if state in ("rain", "snow", "storm", "fog", "cloud", "clear", "night") else ""
        sky_tag = f'<div class="sky{f" sky--{state}" if state else ""}" data-sky="{escape(sky_city)}" aria-hidden="true"><i></i><i></i><i></i></div>'

    capsule_tag = ""
    if capsule:
        opened, day_word, iso, words = capsule
        if opened:
            capsule_tag = (
                f'<section class="capsule is-open" aria-labelledby="capsule-title">'
                f'<h2 class="capsule__title" id="capsule-title">the capsule, opened</h2>'
                f'<p class="capsule__words">{escape(words)}</p>'
                f'<p class="capsule__when">opened {escape(day_word)}</p></section>'
            )
        else:
            capsule_tag = (
                f'<section class="capsule" aria-labelledby="capsule-title" data-capsule="{iso}">'
                f'<h2 class="capsule__title" id="capsule-title">a sealed capsule</h2>'
                f'<p class="capsule__wax" aria-hidden="true">\u2020</p>'
                f'<p class="capsule__when">opens {escape(day_word)}</p>'
                f'<p class="capsule__left" data-capsule-left>\u2026</p></section>'
            )

    here_tag = ""
    if presence_on:  # v3.118: the line fills in from the presence heartbeat; the server renders the first count
        n = int(here or 0)
        here_text = "just you here right now" if n == 1 else f"{n:,} people here right now" if n > 1 else ""
        here_tag = f'<p class="here" data-here{"" if n else " hidden"}><span class="here__dot" aria-hidden="true"></span><span data-here-text>{here_text}</span></p>'

    video_tag = (
        f'<video class="bg-video" autoplay muted loop playsinline preload="metadata" aria-hidden="true"><source src="{escape(bg_video, quote=True)}"></video>'
        if bg_video else ""
    )
    image_style = f"background-image:url('{escape(bg_image, quote=True)}');" if bg_image else ""

    audio_tag = ""
    if audio_enabled:
        audio_tag = (
            f'<div class="player player--{player_style}" data-player{" inert" if entry_screen else ""}>'
            f'<audio preload="none" loop src="{escape(audio, quote=True)}"></audio>'
            f'<button class="player__btn" type="button" aria-label="Play {audio_name}" data-play>{_ic("play")}</button>'
            f'<span class="player__name">{audio_name}</span>'
            f'<span class="player__bars" aria-hidden="true"><i></i><i></i><i></i><i></i></span>'
            f"</div>"
        )
    entry_tag = f'<button class="entry" type="button" data-entry><span class="entry__dagger" aria-hidden="true">†</span><span class="entry__text">{entry_text}</span></button>' if entry_screen else ""
    inert = " inert" if entry_screen else ""  # v3.92: nothing behind the entry screen is reachable until it's dismissed
    cursor_style = f"cursor:url('{cursor.replace(chr(39), '').replace(chr(34), '').replace('<', '').replace('>', '')}') 4 4,auto;" if cursor else ""
    if not cursor and builtin_cursor != "default":
        cursor_style = f"cursor:url(\"{BUILTIN_CURSORS[builtin_cursor]}\") 12 12,auto;"

    name_classes = "name"
    if name_effect in ("glow", "gradient", "shimmer"):
        name_classes += f" name--{name_effect}"
    if glow_name:
        name_classes += " name--halo"

    card_classes = "card" + (f" in-{enter_anim}" if enter_anim and not entry_screen else "") + (" card--gold" if gold_border else "") + age_class + (" is-night" if night and night[0] else "")
    enter_attr = f' data-enter="{enter_anim}"' if enter_anim and entry_screen else ""  # played when the entry screen goes
    accent_rgb, bg_rgb = _hex_rgb(accent), _hex_rgb(bg)
    fx_class = f"fx-{bg_effect}" if bg_effect in ("particles", "stars", "glow", "rain", "snow", "embers", "petals") else ""
    card_border = (
        f"linear-gradient(rgba({bg_rgb},{card_opacity:.2f}),rgba({bg_rgb},{card_opacity:.2f})) padding-box,linear-gradient(135deg,{accent},rgba({accent_rgb},.15),{accent}) border-box"
        if gradient_border else f"rgba({bg_rgb},{card_opacity:.2f})"
    )
    if gold_border:  # v3.113: a gold gradient that turns (via a registered angle property; static gold where unsupported)
        card_border = f"linear-gradient(rgba({bg_rgb},{card_opacity:.2f}),rgba({bg_rgb},{card_opacity:.2f})) padding-box,linear-gradient(var(--ga,135deg),#E6C36B,rgba(230,195,107,.18),#fff2c4,#E6C36B) border-box"
    title = f"{display_name} · misa.lol"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description or ('misa.lol/' + username)}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description or ('misa.lol/' + username)}">
<meta property="og:type" content="profile">
<meta property="og:url" content="https://misa.lol/{username}">
<meta property="og:site_name" content="misa.lol">
<meta property="og:image" content="https://misa.lol/{username}/card.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description or ('misa.lol/' + username)}">
<meta name="twitter:image" content="https://misa.lol/{username}/card.png">
<meta name="theme-color" content="{bg}">
<link rel="icon" href="/images/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{fonts_href}" rel="stylesheet">
<style>
:root{{--accent:{accent};--accent-rgb:{accent_rgb};--text:{text};--bg:{bg};--bg-rgb:{bg_rgb};--icon:{icon_color};--radius:{radius}px;--blur:{blur}px;--font:{font_stack};--fs:{font_scale}}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html,body{{min-height:100%}}
[hidden]{{display:none!important}}
body{{font-family:var(--font);background:var(--bg);color:var(--text);line-height:1.5;-webkit-font-smoothing:antialiased;display:grid;grid-template-columns:minmax(0,1fr);place-items:center;min-height:100svh;padding:28px 16px 88px;overflow-x:hidden;{cursor_style}}}
a{{color:inherit;text-decoration:none}}
button{{font:inherit;color:inherit;background:none;border:0;cursor:pointer}}
.ic{{width:1em;height:1em;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;flex:none}}
.bg-video,.bg-image,.bg-fx,.tint{{position:fixed;inset:0;z-index:0;pointer-events:none}}
.bg-video{{width:100%;height:100%;object-fit:cover;opacity:{bg_opacity:.2f}}}
.bg-image{{background-size:cover;background-position:center;opacity:{bg_opacity:.2f}}}
.tint{{background:linear-gradient(180deg,rgba(var(--bg-rgb),.15),rgba(var(--bg-rgb),.72)),radial-gradient(60% 50% at 50% 40%,rgba(var(--accent-rgb),.22),transparent 70%)}}
.bg-fx.fx-glow{{background:radial-gradient(45% 45% at 50% 55%,rgba(var(--accent-rgb),.35),transparent 70%)}}
.bg-fx.fx-stars{{background-image:radial-gradient(rgba(255,255,255,.55) 1px,transparent 1.4px),radial-gradient(rgba(255,255,255,.3) 1px,transparent 1.4px);background-size:140px 140px,90px 90px;background-position:0 0,40px 60px;animation:drift 90s linear infinite}}
.bg-fx.fx-particles{{background-image:radial-gradient(rgba(var(--accent-rgb),.9) 1.5px,transparent 2px),radial-gradient(rgba(var(--accent-rgb),.5) 1px,transparent 1.5px);background-size:160px 160px,110px 110px;animation:rise 40s linear infinite;opacity:.7}}
.bg-fx.fx-rain{{background-image:repeating-linear-gradient(100deg,transparent 0 22px,rgba(255,255,255,.14) 22px 23px,transparent 23px 38px),repeating-linear-gradient(100deg,transparent 0 31px,rgba(var(--accent-rgb),.22) 31px 32px,transparent 32px 57px);background-size:100% 160px,100% 240px;animation:rain .55s linear infinite;opacity:.8}}
.bg-fx.fx-snow{{background-image:radial-gradient(rgba(255,255,255,.9) 1.6px,transparent 2.4px),radial-gradient(rgba(255,255,255,.6) 1.2px,transparent 2px),radial-gradient(rgba(255,255,255,.35) 1px,transparent 1.6px);background-size:170px 170px,120px 120px,80px 80px;background-position:0 0,50px 30px,20px 70px;animation:snow 14s linear infinite;opacity:.85}}
.bg-fx.fx-embers{{background-image:radial-gradient(rgba(var(--accent-rgb),.95) 1.5px,transparent 2.2px),radial-gradient(rgba(255,180,90,.8) 1.2px,transparent 1.8px),radial-gradient(rgba(255,120,40,.5) 2px,transparent 2.8px);background-size:210px 210px,150px 150px,320px 320px;background-position:0 0,70px 40px,30px 90px;animation:embers 9s linear infinite,flicker 1.3s ease-in-out infinite;opacity:.8}}
.bg-fx.fx-petals{{background-image:radial-gradient(ellipse 5px 9px at 50% 50%,rgba(255,179,209,.95) 60%,transparent 62%),radial-gradient(ellipse 4px 7px at 50% 50%,rgba(255,214,231,.85) 60%,transparent 62%),radial-gradient(ellipse 6px 10px at 50% 50%,rgba(255,150,190,.7) 60%,transparent 62%);background-size:190px 190px,140px 140px,260px 260px;background-position:0 0,60px 30px,120px 80px;animation:petals 16s linear infinite,sway 5s ease-in-out infinite;opacity:.9}}
@keyframes rain{{to{{background-position:-14px 160px,-22px 240px}}}}
@keyframes snow{{to{{background-position:24px 170px,-30px 150px,10px 80px}}}}
@keyframes embers{{to{{background-position:10px -210px,-20px -150px,15px -320px}}}}
@keyframes flicker{{50%{{opacity:.55}}}}
@keyframes petals{{to{{background-position:60px 190px,-40px 140px,80px 260px}}}}
@keyframes sway{{50%{{transform:translateX(14px)}}}}
@keyframes drift{{to{{background-position:140px 140px,130px 150px}}}}
@keyframes rise{{to{{background-position:0 -160px,0 -110px}}}}
.card > *{{max-width:100%}}
.card{{position:relative;z-index:2;width:100%;max-width:460px;min-width:0;grid-template-columns:minmax(0,1fr);padding:40px 30px 30px;border-radius:var(--radius);border:1px solid transparent;background:{card_border};-webkit-backdrop-filter:blur(var(--blur));backdrop-filter:blur(var(--blur));box-shadow:0 40px 100px -40px rgba(0,0,0,.9),0 0 90px -30px rgba(var(--accent-rgb),.45);text-align:center;display:grid;justify-items:center;gap:6px}}
.avatar{{width:96px;height:96px;border-radius:50%;object-fit:cover;border:2px solid rgba(var(--accent-rgb),.55);box-shadow:0 10px 30px -10px rgba(0,0,0,.7),0 0 0 6px rgba(var(--accent-rgb),.12);margin-bottom:10px}}
.avatar--letter{{display:grid;place-items:center;font-weight:800;font-size:38px;background:linear-gradient(135deg,var(--accent),rgba(var(--accent-rgb),.25));color:#fff}}
.name{{font-size:calc(30px * var(--fs));font-weight:800;letter-spacing:-.03em;line-height:1.05;display:inline-flex;align-items:center;gap:10px;flex-wrap:wrap;justify-content:center}}
.name--halo{{text-shadow:0 0 18px rgba(var(--accent-rgb),.65)}}
.name--glow{{color:var(--accent);text-shadow:0 0 14px rgba(var(--accent-rgb),.8),0 0 40px rgba(var(--accent-rgb),.45)}}
.name--gradient{{background:linear-gradient(90deg,var(--accent),var(--text));-webkit-background-clip:text;background-clip:text;color:transparent}}
.name--shimmer{{background:linear-gradient(90deg,var(--text),var(--accent),var(--text));background-size:200% 100%;-webkit-background-clip:text;background-clip:text;color:transparent;animation:shimmer 2.6s linear infinite}}
@keyframes shimmer{{to{{background-position:-200% 0}}}}
.handle{{font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:16px;color:var(--accent);opacity:.95}}
.badges{{display:flex;flex-wrap:wrap;justify-content:center;gap:6px;margin-top:6px}}
.badge{{display:inline-flex;align-items:center;gap:5px;padding:4px 9px 4px 6px;border-radius:999px;font-size:10.5px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;border:1px solid var(--b);color:var(--b);background:rgba(255,255,255,.04)}}
.badge .ic{{width:11px;height:11px;stroke-width:3}}
.location{{display:inline-flex;align-items:center;gap:6px;font-size:13px;opacity:.7;margin-top:4px}}
.location .ic{{width:13px;height:13px;color:var(--icon)}}
.bio{{margin-top:12px;font-size:calc(15px * var(--fs));line-height:1.55;opacity:.85;max-width:100%;text-wrap:pretty;white-space:pre-line;overflow-wrap:anywhere}}
.links{{width:100%;display:grid;gap:9px;margin-top:22px}}
.link{{display:flex;align-items:center;gap:12px;padding:13px 15px;border-radius:calc(var(--radius) * .45);background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);font-size:calc(14px * var(--fs));font-weight:600;text-align:left;transition:transform .2s,background .2s,border-color .2s,box-shadow .2s}}
.link .ic{{width:16px;height:16px;color:var(--icon)}}
.link .ic:last-child{{margin-left:auto;opacity:.45;color:currentColor;width:14px;height:14px}}
.link__label{{min-width:0;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.link__value{{margin-left:auto;font-weight:500;opacity:.7;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:55%}}
a.link:hover{{transform:translateY(-2px);background:rgba(var(--accent-rgb),.16);border-color:rgba(var(--accent-rgb),.5){';box-shadow:0 0 24px -6px rgba(var(--accent-rgb),.7)' if glow_social else ''}}}
a.link:focus-visible{{outline:2px solid var(--accent);outline-offset:3px}}
.links--outline .link{{background:transparent;border:1.5px solid rgba(var(--accent-rgb),.65)}}
.links--outline a.link:hover{{background:rgba(var(--accent-rgb),.12);border-color:var(--accent)}}
.links--ghost{{gap:2px}}
.links--ghost .link{{background:transparent;border:0;border-bottom:1px solid rgba(255,255,255,.08);border-radius:0;padding:12px 4px;font-size:calc(15px * var(--fs))}}
.links--ghost a.link:hover{{transform:none;background:transparent;border-color:var(--accent);box-shadow:none}}
.links--brutal .link{{background:var(--text);color:var(--bg);border:2px solid var(--text);border-radius:6px;box-shadow:5px 5px 0 var(--accent);font-weight:800;text-transform:uppercase;letter-spacing:.04em;font-size:calc(13px * var(--fs))}}
.links--brutal .link .ic{{color:var(--bg)}}
.links--brutal a.link:hover{{transform:translate(2px,2px);box-shadow:3px 3px 0 var(--accent);background:var(--text)}}
.links--glass .link{{background:linear-gradient(180deg,rgba(255,255,255,.18),rgba(255,255,255,.06));border:1px solid rgba(255,255,255,.28);box-shadow:inset 0 1px 0 rgba(255,255,255,.35),0 12px 30px -16px rgba(0,0,0,.8);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px)}}
.avatar-wrap{{position:relative;width:96px;height:96px;margin-bottom:10px;display:grid;place-items:center}}
.avatar-wrap .avatar{{margin-bottom:0}}
.avatar-wrap::before{{content:'';position:absolute;inset:-9px;border-radius:50%;pointer-events:none}}
.frame--ring::before{{background:conic-gradient(from 0deg,var(--accent),transparent 30%,var(--accent) 50%,transparent 80%,var(--accent));-webkit-mask:radial-gradient(farthest-side,transparent calc(100% - 4px),#000 calc(100% - 3px));mask:radial-gradient(farthest-side,transparent calc(100% - 4px),#000 calc(100% - 3px));animation:turn 6s linear infinite}}
.frame--halo::before{{inset:-14px;box-shadow:0 0 0 2px rgba(var(--accent-rgb),.5),0 0 30px 6px rgba(var(--accent-rgb),.45);animation:halo 3s ease-in-out infinite}}
.frame--pixel .avatar{{border-radius:10px;border:0;box-shadow:0 0 0 4px var(--accent),0 0 0 8px var(--bg),0 0 0 11px var(--accent);image-rendering:pixelated}}
.frame--pixel::before{{display:none}}
.frame--petals::before{{inset:-12px;border:4px dotted #ffb3d1;animation:turn 18s linear infinite;filter:drop-shadow(0 0 6px rgba(255,179,209,.7))}}
@keyframes turn{{to{{transform:rotate(360deg)}}}}
@keyframes halo{{50%{{box-shadow:0 0 0 2px rgba(var(--accent-rgb),.8),0 0 44px 10px rgba(var(--accent-rgb),.6)}}}}
:focus-visible{{outline:2px solid var(--accent);outline-offset:3px}}
.sr-only{{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}}
.foot{{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px 12px;width:100%;margin-top:22px;font-size:12px;opacity:.7}}
.foot .views,.foot .brand{{white-space:nowrap}}
.views{{display:inline-flex;align-items:center;gap:6px;font-variant-numeric:tabular-nums}}
.views .ic{{width:14px;height:14px}}
.report{{margin-left:auto;background:none;border:0;color:inherit;opacity:.55;font:inherit;font-size:11px;letter-spacing:.08em;text-transform:uppercase;cursor:pointer;padding:8px 6px;margin-block:-8px}}
.report:hover{{opacity:1}}
.report-form[hidden]{{display:none}}
.report-form{{margin:14px 0 0;display:grid;gap:8px;padding:14px;border-radius:12px;border:1px solid rgba(255,255,255,.14);background:rgba(0,0,0,.35);font-size:13px}}
.report-form__t{{font-weight:600}}
.report-form select,.report-form textarea{{font:inherit;color:inherit;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.14);border-radius:8px;padding:8px 10px}}
.report-form__row{{display:flex;gap:8px}}
.report-form button{{font:inherit;font-weight:600;padding:8px 14px;border-radius:999px;border:1px solid rgba(255,255,255,.2);background:rgba(255,255,255,.08);color:inherit;cursor:pointer}}
.report-form__msg{{min-height:1em;opacity:.8}}
.brand{{margin-left:auto;display:inline-flex;align-items:center;gap:6px;padding:8px 12px;border-radius:999px;border:1px solid rgba(255,255,255,.12);font-size:11.5px;font-weight:600;letter-spacing:.02em;opacity:.85;transition:opacity .2s,border-color .2s}}
.brand:hover{{opacity:1;border-color:rgba(var(--accent-rgb),.6)}}
.brand b{{color:var(--accent);font-weight:800}}
.player{{position:fixed;left:16px;bottom:16px;z-index:3;display:flex;align-items:center;gap:10px;padding:8px 14px 8px 8px;border-radius:999px;background:rgba(var(--bg-rgb),.78);border:1px solid rgba(255,255,255,.12);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);font-size:12.5px;max-width:min(320px,calc(100vw - 32px))}}
.player__btn{{width:34px;height:34px;border-radius:50%;display:grid;place-items:center;background:var(--accent);color:#fff;flex:none}}
.player__btn .ic{{width:14px;height:14px}}
.player__name{{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.player__bars{{display:none;align-items:flex-end;gap:2px;height:14px}}
.player__bars i{{width:3px;height:6px;background:var(--accent);border-radius:2px;animation:bar 1s ease-in-out infinite}}
.player__bars i:nth-child(2){{animation-delay:-.25s}}.player__bars i:nth-child(3){{animation-delay:-.5s}}.player__bars i:nth-child(4){{animation-delay:-.75s}}
.player.is-playing .player__bars{{display:flex}}
@keyframes bar{{0%,100%{{height:5px}}50%{{height:14px}}}}
.player--minimal{{padding:0;background:none;border:0;backdrop-filter:none;-webkit-backdrop-filter:none;gap:0}}
.player--minimal .player__btn{{width:44px;height:44px;box-shadow:0 10px 30px -10px rgba(0,0,0,.8),0 0 0 1px rgba(255,255,255,.12)}}
.player--minimal .player__name,.player--minimal .player__bars{{position:absolute;left:52px;top:50%;transform:translateY(-50%);white-space:nowrap;font-size:12px;padding:6px 10px;border-radius:999px;background:rgba(var(--bg-rgb),.85);opacity:0;transition:opacity .2s;pointer-events:none}}
.player--minimal .player__bars{{display:none}}
.player--minimal:hover .player__name,.player--minimal:focus-within .player__name{{opacity:1}}
.player--vinyl{{padding:6px 14px 6px 6px}}
.player--vinyl .player__btn{{width:44px;height:44px;background:radial-gradient(circle at 50% 50%,var(--accent) 0 26%,#111 27% 30%,#222 31% 34%,#111 35% 38%,#232323 39% 42%,#111 43% 46%,#1e1e1e 47% 50%,#101010 51%);box-shadow:0 0 0 1px rgba(255,255,255,.15),0 10px 24px -8px rgba(0,0,0,.8)}}
.player--vinyl .player__btn .ic{{width:12px;height:12px;color:#fff;filter:drop-shadow(0 0 2px rgba(0,0,0,.8))}}
.player--vinyl.is-playing .player__btn{{animation:spin 2.4s linear infinite}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
.entry{{position:fixed;inset:0;z-index:10;display:grid;place-content:center;gap:10px;background:rgba(var(--bg-rgb),.92);-webkit-backdrop-filter:blur(20px);backdrop-filter:blur(20px);color:var(--text);text-align:center}}
.entry__dagger{{font-size:64px;font-weight:800;color:var(--accent);line-height:1}}
.entry__text{{font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:26px;letter-spacing:-.01em;opacity:.9;animation:pulse 2.2s ease-in-out infinite}}
@keyframes pulse{{50%{{opacity:.5}}}}
.blocks{{width:100%;display:grid;gap:10px;margin-top:18px;text-align:left}}
.blk{{margin:0;max-width:100%;overflow-wrap:anywhere}}
.blk--h{{font-size:11.5px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;opacity:.7;margin-top:6px}}
.blk--p{{font-size:calc(14px * var(--fs));line-height:1.55;opacity:.85;white-space:pre-line}}
.blk--q{{font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:calc(19px * var(--fs));line-height:1.35;padding-left:14px;border-left:2px solid var(--accent);white-space:pre-line}}
.blk--hr{{border:0;height:1px;background:linear-gradient(90deg,transparent,rgba(255,255,255,.22) 42%,transparent 45%,transparent 55%,rgba(255,255,255,.22) 58%,transparent);position:relative;margin:8px 0;overflow:visible}}
.blk--hr::after{{content:'†';position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);color:var(--accent);font-size:14px;line-height:1}}
.blk--now{{display:flex;align-items:center;gap:8px;font-size:calc(13px * var(--fs));padding:9px 12px;border-radius:999px;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.05);width:max-content;max-width:100%}}
.blk--clock{{display:flex;align-items:baseline;gap:6px;font-size:calc(13px * var(--fs));padding:9px 14px;border-radius:999px;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.05);width:max-content;max-width:100%;font-variant-numeric:tabular-nums}}
.blk--clock .blk__k{{font-size:inherit;letter-spacing:0;text-transform:none;opacity:.7}}
.blk--clock .blk__time{{font-weight:800;font-size:calc(15px * var(--fs));letter-spacing:-.01em}}
.blk__colon{{animation:colon 1s steps(1) infinite}}
.blk--np{{display:flex;align-items:center;gap:10px;font-size:calc(13px * var(--fs));padding:8px 14px 8px 9px;border-radius:999px;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.05);width:max-content;max-width:100%;text-align:left}}
.np__disc{{width:26px;height:26px;border-radius:50%;flex:none;background:radial-gradient(circle,var(--accent) 0 3px,var(--bg) 3.5px 5px,#1c1c1f 5.5px 8.5px,#0b0b0d 9px 10px,#1c1c1f 10.5px 12px,#0b0b0d 12.5px);box-shadow:0 0 0 1px rgba(255,255,255,.14),0 4px 12px -6px rgba(0,0,0,.9)}}
.blk--np.is-live .np__disc{{animation:spin 2.4s linear infinite}}
.np__k{{font-size:10px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;opacity:.6;white-space:nowrap}}
.np__t{{font-weight:600;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
a.np__t:hover{{color:var(--accent)}}
.np__bars{{display:none;align-items:flex-end;gap:2px;height:14px}}
.blk--np.is-live .np__bars{{display:flex}}
.np__bars i{{width:3px;height:6px;background:var(--accent);border-radius:2px;animation:bar 1s ease-in-out infinite}}
.np__bars i:nth-child(2){{animation-delay:-.33s}}.np__bars i:nth-child(3){{animation-delay:-.66s}}
.blk--wx{{display:flex;align-items:center;gap:9px;font-size:calc(13px * var(--fs));padding:9px 14px 9px 12px;border-radius:999px;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.05);width:max-content;max-width:100%}}
.blk--wx .ic{{width:18px;height:18px;color:var(--icon);stroke-width:1.8}}
.blk__deg{{font-weight:800;font-variant-numeric:tabular-nums}}
@keyframes colon{{50%{{opacity:.3}}}}
.mood{{position:fixed;inset:0;z-index:1;pointer-events:none;opacity:0;transition:opacity 1.6s ease}}
[data-mood=dawn] .mood{{opacity:1;background:linear-gradient(180deg,rgba(255,176,140,.26),rgba(255,120,150,.12) 45%,rgba(40,14,34,.3))}}
[data-mood=day] .mood{{opacity:1;background:linear-gradient(180deg,rgba(255,250,240,.11),rgba(190,214,255,.07) 60%,rgba(255,255,255,.03))}}
[data-mood=dusk] .mood{{opacity:1;background:linear-gradient(180deg,rgba(255,122,64,.2),rgba(128,44,132,.2) 55%,rgba(16,8,40,.4))}}
[data-mood=night] .mood{{opacity:1;background:radial-gradient(60% 50% at 50% 28%,rgba(var(--accent-rgb),.12),transparent 70%),linear-gradient(180deg,rgba(0,2,12,.28),rgba(0,0,0,.5))}}
.secret{{width:100%;display:grid;gap:8px;margin-top:14px}}
.secret.in-glitch{{animation:in-glitch .9s steps(1) both}}
.secret__k{{font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:14px;color:var(--accent)}}
.secret .link{{border-color:rgba(var(--accent-rgb),.6);box-shadow:0 0 28px -8px rgba(var(--accent-rgb),.8)}}
.secret__ask{{width:100%;margin-top:14px}}
.secret__ask input{{width:100%;font:inherit;color:inherit;text-align:center;background:rgba(255,255,255,.06);border:1px dashed rgba(var(--accent-rgb),.6);border-radius:999px;padding:10px 14px;letter-spacing:.08em}}
.secret__ask input::placeholder{{color:inherit;opacity:.5}}
.secret__ask.is-wrong input{{animation:wrong .4s ease}}
@keyframes wrong{{25%{{transform:translateX(-6px)}}75%{{transform:translateX(6px)}}}}
.here{{display:inline-flex;align-items:center;gap:8px;margin-top:20px;font-size:12px;letter-spacing:.03em;opacity:.82}}
.here__dot{{width:7px;height:7px;border-radius:50%;background:var(--accent);box-shadow:0 0 0 0 rgba(var(--accent-rgb),.6);animation:herepulse 2.2s ease-out infinite}}
@keyframes herepulse{{to{{box-shadow:0 0 0 9px rgba(var(--accent-rgb),0)}}}}
.here + .foot{{margin-top:14px}}
.fresh{{display:inline-flex;align-items:center;padding:3px 9px;border-radius:999px;border:1px dashed rgba(255,255,255,.35);font-size:10.5px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;opacity:.8;margin-top:8px}}
.seal{{position:absolute;top:14px;right:14px;width:46px;height:46px;border-radius:50%;display:grid;place-items:center;font-size:22px;font-weight:800;line-height:1;color:#fff;background:radial-gradient(circle at 35% 30%,rgba(255,255,255,.38),transparent 42%),radial-gradient(circle at 62% 72%,rgba(0,0,0,.35),transparent 52%),var(--accent);box-shadow:0 3px 0 rgba(0,0,0,.35),0 10px 20px -8px rgba(0,0,0,.85),inset 0 0 0 3px rgba(255,255,255,.14),inset 0 0 0 5px rgba(0,0,0,.14);transform:rotate(-12deg);z-index:3}}
.seal::before{{content:'';position:absolute;inset:-6px;border-radius:50%;border:2px dashed rgba(255,255,255,.22)}}
.seal b{{position:absolute;right:-10px;bottom:-8px;font-size:9px;letter-spacing:.06em;padding:2px 6px;border-radius:999px;background:var(--bg);color:var(--text);border:1px solid rgba(255,255,255,.22);transform:rotate(12deg)}}
.seal--gold{{background:radial-gradient(circle at 35% 30%,rgba(255,255,255,.5),transparent 42%),radial-gradient(circle at 62% 72%,rgba(120,80,0,.45),transparent 52%),#E6C36B;color:#3a2b00}}
.patina{{position:absolute;inset:0;border-radius:inherit;pointer-events:none;z-index:-1;opacity:.9;background:radial-gradient(120% 90% at 50% 40%,transparent 55%,rgba(0,0,0,.4)),repeating-linear-gradient(115deg,rgba(255,255,255,.028) 0 2px,transparent 2px 7px),radial-gradient(circle at 10% 90%,rgba(230,195,107,.12),transparent 30%),radial-gradient(circle at 90% 10%,rgba(230,195,107,.09),transparent 28%)}}
.since{{white-space:nowrap;opacity:.85}}
.board{{width:100%;margin-top:26px;display:grid;gap:12px;justify-items:center;text-align:left}}
.board__title{{font-family:'Caveat','Segoe Print','Bradley Hand',cursive;font-weight:600;font-size:24px;color:var(--accent);justify-self:start;line-height:1}}
.wall{{list-style:none;width:100%;display:grid;grid-template-columns:repeat(auto-fill,minmax(88px,1fr));gap:10px}}
.tile{{aspect-ratio:10/7;border-radius:6px;background:radial-gradient(120% 90% at 30% 20%,rgba(255,255,255,.06),transparent 60%),#151b18;border:1px solid rgba(255,255,255,.1);box-shadow:inset 0 0 26px rgba(0,0,0,.55),0 8px 20px -14px rgba(0,0,0,.9);transform:rotate(var(--r,0deg));padding:4px}}
.doodle{{display:block;width:100%;height:100%;opacity:.95;filter:drop-shadow(0 0 1px rgba(255,255,255,.25))}}
.board__empty{{font-size:13px;opacity:.7;justify-self:start}}
.board__open{{padding:9px 16px;border-radius:999px;border:1px dashed rgba(var(--accent-rgb),.6);color:var(--accent);font-family:'Caveat','Segoe Print','Bradley Hand',cursive;font-weight:600;font-size:18px;line-height:1;transition:background .2s,transform .2s}}
.board__open:hover{{background:rgba(var(--accent-rgb),.12);transform:translateY(-1px)}}
.board__form{{width:100%;display:grid;gap:10px;padding:12px;border-radius:12px;border:1px solid rgba(255,255,255,.12);background:rgba(0,0,0,.3)}}
.board__canvas{{width:100%;aspect-ratio:10/7;display:block;border-radius:8px;background:radial-gradient(120% 90% at 30% 20%,rgba(255,255,255,.06),transparent 60%),#151b18;border:1px solid rgba(255,255,255,.12);box-shadow:inset 0 0 26px rgba(0,0,0,.55);touch-action:none;cursor:crosshair}}
.board__palette{{display:flex;gap:8px;align-items:center}}
.board__chalk{{position:relative;width:28px;height:28px;display:grid;place-items:center;cursor:pointer}}
.board__chalk input{{position:absolute;inset:0;opacity:0;margin:0;cursor:pointer}}
.board__chalk i{{width:16px;height:16px;border-radius:50%;background:var(--c);box-shadow:0 0 0 2px rgba(255,255,255,.12);transition:transform .15s,box-shadow .15s}}
.board__chalk input:checked + i{{transform:scale(1.25);box-shadow:0 0 0 2px var(--text)}}
.board__chalk input:focus-visible + i{{outline:2px solid var(--accent);outline-offset:3px}}
.board__row{{display:flex;gap:8px;flex-wrap:wrap}}
.board__row button{{padding:9px 14px;border-radius:999px;font-size:13px;font-weight:600;border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.06)}}
.board__row button[type=submit]{{background:var(--accent);border-color:var(--accent);color:#fff}}
.board__msg{{font-size:12px;opacity:.8;min-height:1em}}
.board__msg:empty{{display:none}}
.odo{{display:grid;justify-items:center;gap:8px;width:100%;margin-top:24px}}
.odo__label{{font-size:10.5px;letter-spacing:.2em;text-transform:uppercase;opacity:.6}}
.odo__digits{{display:inline-flex;gap:3px;font-family:ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;font-size:24px;font-weight:700;line-height:1}}
.odo__d{{position:relative;display:block;width:1.1em;height:1.35em;overflow:hidden;border-radius:4px}}
.odo__col{{display:block;transform:translateY(calc(var(--n) * -1.35em));transition:transform 1.6s cubic-bezier(.2,.8,.2,1);transition-delay:calc(var(--i) * .08s)}}
.odo__col i{{display:block;height:1.35em;line-height:1.35em;font-style:normal;text-align:center}}
.odo--odometer .odo__d{{background:linear-gradient(180deg,#1c1c20,#050506 46%,#0a0a0c 54%,#1c1c20);border:1px solid rgba(255,255,255,.14);box-shadow:inset 0 2px 5px rgba(0,0,0,.9),0 1px 0 rgba(255,255,255,.05);color:#EEE8E2}}
.odo--odometer .odo__d:last-child{{color:var(--accent)}}
.odo--odometer .odo__d::after{{content:'';position:absolute;left:0;right:0;top:50%;height:1px;background:rgba(0,0,0,.7);pointer-events:none}}
.odo--lcd .odo__digits{{gap:1px;padding:7px 10px;border-radius:7px;background:#08090a;border:1px solid rgba(255,255,255,.1);box-shadow:inset 0 0 18px rgba(0,0,0,.9),0 0 22px -8px rgba(var(--accent-rgb),.6);color:var(--accent);text-shadow:0 0 7px rgba(var(--accent-rgb),.9),0 0 18px rgba(var(--accent-rgb),.4)}}
.odo--lcd .odo__d::before{{content:'8';position:absolute;inset:0;text-align:center;line-height:1.35em;opacity:.13;text-shadow:none}}
.odo--flip .odo__digits{{gap:4px}}
.odo--flip .odo__d{{background:linear-gradient(180deg,#1d1d22 50%,#0f0f12 50%);color:#EEE8E2;border-radius:5px;box-shadow:0 3px 0 rgba(0,0,0,.55),inset 0 0 0 1px rgba(255,255,255,.07)}}
.odo--flip .odo__d::after{{content:'';position:absolute;left:0;right:0;top:50%;height:2px;background:rgba(0,0,0,.85);pointer-events:none}}
.blk__k{{font-size:10px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;opacity:.6}}
.blk__dot{{width:7px;height:7px;border-radius:50%;background:#3ddc84;box-shadow:0 0 10px #3ddc84;animation:pulse 2.2s ease-in-out infinite;flex:none}}
.book{{width:100%;margin-top:24px;text-align:left}}
.book__title{{font-family:'Caveat','Segoe Print',cursive;font-size:26px;font-weight:600;color:var(--accent);transform:rotate(-2deg);display:inline-block}}
.slips{{list-style:none;display:grid;gap:10px;margin-top:8px}}
.slip{{position:relative;padding:10px 14px 9px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);border-radius:3px;transform:rotate(var(--r,0deg));box-shadow:0 8px 20px -14px rgba(0,0,0,.9);display:grid;gap:2px}}
.slip::before{{content:'';position:absolute;left:50%;top:-6px;width:38px;height:12px;transform:translateX(-50%) rotate(-3deg);background:rgba(var(--accent-rgb),.55);opacity:.8;border-radius:1px}}
.slip__line{{font-family:'Caveat','Segoe Print',cursive;font-size:21px;line-height:1.15;overflow-wrap:anywhere}}
.slip__who{{font-size:11px;letter-spacing:.06em;opacity:.65;text-transform:lowercase}}
.book__empty{{font-size:13px;opacity:.7;margin-top:6px}}
.book__open{{margin-top:12px;padding:9px 16px;border-radius:999px;border:1px dashed rgba(var(--accent-rgb),.7);color:var(--accent);font-family:'Caveat','Segoe Print',cursive;font-size:19px;font-weight:600}}
.book__open:hover{{background:rgba(var(--accent-rgb),.12)}}
.book__form{{margin-top:12px;display:grid;gap:8px;padding:14px;border-radius:12px;border:1px solid rgba(255,255,255,.14);background:rgba(0,0,0,.35);font-size:13px}}
.book__form[hidden]{{display:none}}
.book__lab{{display:grid;gap:4px;font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;opacity:.85}}
.book__lab input{{font:inherit;font-size:14px;letter-spacing:0;text-transform:none;color:inherit;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.14);border-radius:8px;padding:9px 10px}}
.book__row{{display:flex;gap:8px}}
.book__row button{{font:inherit;font-weight:600;padding:8px 14px;border-radius:999px;border:1px solid rgba(255,255,255,.2);background:rgba(255,255,255,.08);color:inherit;cursor:pointer}}
.book__row button[type=submit]{{background:var(--accent);border-color:var(--accent);color:#fff}}
.book__msg{{min-height:1em;opacity:.85;font-family:'Caveat','Segoe Print',cursive;font-size:18px}}
/* v3.128: the ask box — a question in, an answer in the owner's hand */
.asks{{margin-top:26px;display:grid;gap:10px}}
.asks__title{{font-family:'Caveat','Segoe Print',cursive;font-size:26px;font-weight:600;color:var(--accent);transform:rotate(-1.5deg);display:inline-block;justify-self:start}}
.asks__form{{display:flex;flex-wrap:wrap;gap:8px;align-items:center}}
.asks__lab{{flex:1 1 190px;min-width:0;display:grid}}
.asks__lab input{{font:inherit;font-size:14px;color:inherit;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.14);border-radius:999px;padding:10px 16px;width:100%}}
.asks__lab input::placeholder{{color:inherit;opacity:.5}}
.asks__lab input:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
.asks__form button{{font:inherit;font-weight:600;font-size:13px;padding:10px 16px;border-radius:999px;border:1px solid var(--accent);background:var(--accent);color:#fff;cursor:pointer}}
.asks__form button:hover{{filter:brightness(1.08)}}
.asks__msg{{flex:1 0 100%;min-height:1em;font-family:'Caveat','Segoe Print',cursive;font-size:18px;opacity:.85;text-align:left}}
.asks__empty{{font-size:13px;opacity:.7}}
.qas{{list-style:none;display:grid;gap:12px;margin-top:2px}}
.qa{{display:grid;gap:5px;padding:12px 14px;border-radius:12px;border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.045);text-align:left}}
.qa__q{{position:relative;padding-left:20px;font-size:13.5px;line-height:1.45;opacity:.72;overflow-wrap:anywhere}}
.qa__q::before{{content:'?';position:absolute;left:0;top:-1px;font-family:'Caveat','Segoe Print',cursive;font-size:22px;line-height:1;color:var(--accent);opacity:.9}}
.qa__a{{font-family:'Caveat','Segoe Print',cursive;font-size:21px;line-height:1.25;overflow-wrap:anywhere}}
/* v3.129: the time capsule — words the server keeps back until the day */
.capsule{{margin-top:22px;display:grid;gap:6px;justify-items:center;text-align:center;padding:16px 18px;border-radius:14px;border:1px dashed rgba(var(--accent-rgb),.5);background:rgba(0,0,0,.22)}}
.capsule__title{{font-family:'Caveat','Segoe Print',cursive;font-size:24px;font-weight:600;color:var(--accent);transform:rotate(-1.5deg)}}
.capsule__wax{{width:44px;height:44px;display:grid;place-items:center;border-radius:50%;background:radial-gradient(circle at 35% 30%,rgba(var(--accent-rgb),.95),rgba(var(--accent-rgb),.55));color:#fff;font-size:24px;line-height:1;box-shadow:0 6px 18px -8px rgba(0,0,0,.8),inset 0 0 0 2px rgba(255,255,255,.18)}}
.capsule__when{{font-size:11px;letter-spacing:.14em;text-transform:uppercase;opacity:.7}}
.capsule__left{{font-family:'Caveat','Segoe Print',cursive;font-size:20px;opacity:.9;min-height:1em}}
.capsule.is-open{{border-style:solid;border-color:rgba(255,255,255,.14);background:rgba(255,255,255,.05)}}
.capsule__words{{font-family:'Caveat','Segoe Print',cursive;font-size:21px;line-height:1.3;overflow-wrap:anywhere;text-align:left;justify-self:stretch}}
/* v3.146: the moon — tonight's real phase, one path, no network and nothing cached */
.moonw{{position:absolute;top:18px;left:18px;z-index:3;display:block;line-height:0;opacity:.9;filter:drop-shadow(0 0 10px rgba(255,255,255,.18))}}
.moonw--full{{filter:drop-shadow(0 0 16px rgba(255,255,255,.5))}}
.moon{{display:block;overflow:visible}}
.moon__lit{{fill:#efeae2}}
.moon__dark{{fill:rgba(255,255,255,.09)}}
@media (max-width:420px){{.moonw{{top:14px;left:14px}}}}
/* v3.144: neighbours — pages that named each other, and only those */
.nb{{margin-top:22px;text-align:center}}
.nb__title{{font-family:'Caveat','Segoe Print',cursive;font-size:calc(24px * var(--fs));font-weight:600;color:var(--accent);transform:rotate(-1.2deg);margin-bottom:8px}}
.nb__list{{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;justify-content:center;gap:8px}}
.nb__one a{{display:inline-flex;align-items:center;gap:8px;padding:8px 13px;border-radius:999px;border:1px solid rgba(255,255,255,.14);background:rgba(0,0,0,.2);color:var(--text);font-size:calc(13px * var(--fs));font-weight:600;text-decoration:none;transition:border-color .2s,background .2s}}
.nb__one a:hover{{border-color:var(--nb,rgba(var(--accent-rgb),.8));background:rgba(255,255,255,.06)}}
.nb__dot{{width:8px;height:8px;border-radius:50%;flex:none;background:var(--nb,var(--accent))}}
.nb__one small{{font-size:.8em;font-weight:400;opacity:.6}}
.nb__empty{{font-family:'Caveat','Segoe Print',cursive;font-size:calc(18px * var(--fs));opacity:.7}}
/* v3.143: the archive — the bar on a page you are reading backwards */
.wasat{{margin:14px 0 4px;padding:10px 14px;border-radius:11px;border:1px dashed rgba(var(--accent-rgb),.55);background:rgba(0,0,0,.25);font-size:calc(13px * var(--fs));line-height:1.45;overflow-wrap:anywhere}}
.wasat b{{color:var(--accent);font-weight:600}}
.wasat a{{color:var(--text);text-decoration:underline;text-underline-offset:3px}}
/* v3.142: the night shift — the line that says why there is more here at this hour */
.nightfall{{margin-top:12px;font-family:'Caveat','Segoe Print',cursive;font-size:calc(19px * var(--fs));color:var(--accent);opacity:.9;overflow-wrap:anywhere}}
.card.is-night{{box-shadow:0 40px 100px -40px rgba(0,0,0,.95),0 0 90px -30px rgba(var(--accent-rgb),.65)}}
/* v3.138: the draw — one line, dealt to this visitor, theirs for the day */
.draw{{margin-top:22px;display:grid;justify-items:center;gap:8px}}
.draw__title{{font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--accent);opacity:.85}}
.draw__card{{font-family:'Caveat','Segoe Print',cursive;font-size:calc(23px * var(--fs));line-height:1.32;text-align:center;overflow-wrap:anywhere;padding:16px 22px;border-radius:12px;border:1px solid rgba(255,255,255,.12);background:rgba(0,0,0,.2);box-shadow:0 14px 30px -22px #000;transform:rotate(-1.1deg);animation:dealt .7s cubic-bezier(.2,.7,.2,1) both}}
@keyframes dealt{{from{{opacity:0;transform:rotate(-9deg) translateY(14px) scale(.96)}}to{{opacity:1;transform:rotate(-1.1deg)}}}}
/* v3.136: the tally — one question, and the count scratched on the card the way you'd count days on a wall */
.tal{{margin-top:22px;text-align:center}}
.tal__title{{font-family:'Caveat','Segoe Print',cursive;font-size:calc(25px * var(--fs));font-weight:600;color:var(--accent);transform:rotate(-1deg);margin-bottom:10px;overflow-wrap:anywhere}}
.tal__list{{list-style:none;margin:0;padding:0;display:grid;gap:9px}}
.tal__row{{display:grid;grid-template-columns:minmax(0,1fr) auto auto;align-items:center;gap:10px;text-align:left}}
.tal__pick{{font:inherit;font-size:calc(14px * var(--fs));text-align:left;padding:9px 13px;border-radius:10px;border:1px dashed rgba(var(--accent-rgb),.45);background:rgba(0,0,0,.16);color:var(--text);cursor:pointer;overflow-wrap:anywhere;transition:background .2s,border-color .2s}}
.tal__pick:hover{{background:rgba(var(--accent-rgb),.12);border-color:rgba(var(--accent-rgb),.8)}}
.tal.is-done .tal__pick{{cursor:default;border-style:solid;border-color:rgba(255,255,255,.12);background:transparent}}
.tal.is-done .tal__pick:hover{{background:transparent;border-color:rgba(255,255,255,.12)}}
.tal__row.is-mine .tal__pick{{border-color:rgba(var(--accent-rgb),.8);background:rgba(var(--accent-rgb),.1)}}
.tal__row.is-mine .tal__pick::after{{content:' — yours';font-family:'Caveat','Segoe Print',cursive;font-size:1.25em;color:var(--accent)}}
.tal__marks{{display:flex;align-items:flex-end;gap:9px;min-height:20px}}
.mark{{position:relative;display:flex;gap:3px;padding-right:2px}}
.mark i{{display:block;width:2px;height:19px;background:var(--text);opacity:.85;border-radius:1px;transform:rotate(var(--lean,2deg))}}
.mark i:nth-child(2){{--lean:-2deg;height:18px}}
.mark i:nth-child(3){{--lean:3deg;height:20px}}
.mark i:nth-child(4){{--lean:-1deg;height:18px}}
.mark--five::after{{content:'';position:absolute;left:-3px;right:-3px;top:50%;height:2px;background:var(--accent);border-radius:1px;transform:rotate(-19deg)}}
.tal__n{{font-family:'Caveat','Segoe Print',cursive;font-size:calc(19px * var(--fs));opacity:.85;min-width:1.6em;text-align:right}}
.tal__msg{{min-height:1em;margin-top:8px;font-family:'Caveat','Segoe Print',cursive;font-size:calc(18px * var(--fs));opacity:.9}}
@media (max-width:420px){{.tal__row{{grid-template-columns:minmax(0,1fr) auto;gap:6px 8px}}.tal__marks{{grid-column:1/2}}.tal__n{{grid-column:2/3}}}}
/* v3.135: the page has a back — a second face the card turns over to show. Without JS the two faces simply
   stack, so the writing on the back is still there to read; the script turns the stack into a card that flips. */
.flip{{position:relative;z-index:2;width:100%;max-width:460px;display:grid;gap:18px;justify-items:center}}
.flip .card{{max-width:none;width:100%}}
.card--back{{text-align:left;justify-items:stretch;gap:14px;padding:36px 30px 34px}}
.back__title{{font-family:'Caveat','Segoe Print',cursive;font-size:calc(29px * var(--fs));font-weight:600;color:var(--accent);transform:rotate(-1.4deg);text-align:center;margin-bottom:2px}}
.back__p{{font-family:'Caveat','Segoe Print',cursive;font-size:calc(21px * var(--fs));line-height:1.42;overflow-wrap:anywhere;color:var(--text)}}
.card--back .blocks{{width:100%}}
.flip .card,.flip .card--back{{padding-bottom:56px}}
.dogear{{position:absolute;right:0;bottom:0;width:38px;height:38px;padding:0;border:0;background:none;cursor:pointer;border-bottom-right-radius:var(--radius);overflow:hidden}}
.dogear::before{{content:'';position:absolute;right:-1px;bottom:-1px;border-style:solid;border-width:0 0 28px 28px;border-color:transparent transparent rgba(var(--accent-rgb),.5) transparent;filter:drop-shadow(-2px -2px 4px rgba(0,0,0,.55));transition:border-width .25s var(--ease,ease),border-color .25s}}
.dogear:hover::before,.dogear:focus-visible::before{{border-width:0 0 36px 36px;border-color:transparent transparent rgba(var(--accent-rgb),.8) transparent}}
.dogear__hint{{position:absolute;right:34px;bottom:14px;white-space:nowrap;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);opacity:0;transform:translateX(6px);transition:opacity .25s,transform .25s;pointer-events:none}}
.dogear:hover ~ .dogear__hint,.dogear:focus-visible ~ .dogear__hint{{opacity:.85;transform:none}}
/* with the script: one card, two faces */
.flip.flip--on{{gap:0;perspective:1800px}}
.flip--on .card,.flip--on .card--back{{grid-area:1/1;backface-visibility:hidden;-webkit-backface-visibility:hidden;transition:transform .75s cubic-bezier(.2,.7,.2,1)}}
.flip--on .card{{transform:rotateY(0)}}
.flip--on .card--back{{transform:rotateY(180deg)}}
.flip--on.is-back .card{{transform:rotateY(-180deg)}}
.flip--on.is-back .card--back{{transform:rotateY(0)}}
.flip--on{{align-items:start;transition:height .75s cubic-bezier(.2,.7,.2,1)}}
/* v3.134: the vigil — candles visitors light, that burn down and go out on their own */
.vigil{{margin-top:22px;text-align:center}}
.vigil__title{{font-family:'Caveat','Segoe Print',cursive;font-size:24px;font-weight:600;color:var(--accent);transform:rotate(-1.2deg);margin-bottom:6px}}
.shelf{{list-style:none;margin:0 0 4px;padding:0 6px 10px;display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:center;gap:12px 10px;min-height:86px;border-bottom:1px solid rgba(255,255,255,.12)}}
.candle{{position:relative;width:16px;display:flex;flex-direction:column;align-items:center;justify-content:flex-end}}
.candle__wax{{display:block;width:11px;border-radius:4px 4px 2px 2px;background:linear-gradient(180deg,#f6f0e8,#cdc3b6 60%,#a89c8d);box-shadow:inset -2px 0 0 rgba(0,0,0,.16);height:calc(6px + 56px * var(--h))}}
.candle__pool{{display:block;height:4px;border-radius:50%;background:rgba(238,232,226,.5);width:calc(11px + 9px * (1 - var(--h)))}}
.candle__flame{{position:absolute;left:50%;bottom:calc(10px + 56px * var(--h));width:7px;height:11px;margin-left:-3.5px;border-radius:50% 50% 46% 46%/62% 62% 38% 38%;background:radial-gradient(60% 60% at 50% 72%,#fff6d8,#ffc55c 55%,rgba(var(--accent-rgb),.85));box-shadow:0 0 12px 3px rgba(255,180,80,.45);transform-origin:50% 100%;animation:flicker 1.6s ease-in-out infinite}}
.candle:nth-child(3n) .candle__flame{{animation-duration:2.3s}}
.candle:nth-child(3n+1) .candle__flame{{animation-duration:1.9s;animation-delay:-.6s}}
@keyframes flicker{{0%,100%{{transform:scale(1) skewX(0deg)}}35%{{transform:scale(1.14,.9) skewX(5deg)}}70%{{transform:scale(.92,1.1) skewX(-4deg)}}}}
.candle.is-out .candle__flame{{animation:none;opacity:0;transform:translateY(-10px) scale(.4);transition:opacity .7s,transform .7s}}
.candle.is-out{{opacity:.35;transition:opacity .7s}}
.shelf:empty{{min-height:34px}}
@media (max-width:520px){{.shelf{{gap:10px 6px;padding-left:2px;padding-right:2px}}.candle{{width:13px}}}}
.vigil__note{{font-size:12px;letter-spacing:.1em;text-transform:uppercase;opacity:.62}}
.vigil__empty{{font-family:'Caveat','Segoe Print',cursive;font-size:19px;opacity:.75}}
.vigil__light{{margin-top:8px;font:inherit;font-size:13px;padding:7px 16px;border-radius:999px;border:1px dashed rgba(var(--accent-rgb),.6);background:transparent;color:var(--accent);cursor:pointer}}
.vigil__light:hover{{background:rgba(var(--accent-rgb),.12)}}
.vigil__light[disabled]{{opacity:.5;cursor:default;border-style:solid}}
.vigil__msg{{min-height:1em;margin-top:6px;font-family:'Caveat','Segoe Print',cursive;font-size:18px;opacity:.9}}
/* v3.130: the sky — the real weather where the owner is, drawn over the page. Never in the way: fixed, behind the card, no pointer events. */
/* v3.132: the line for someone who has been here before — written by their browser, out of their own storage */
.again{{margin-top:10px;font-family:'Caveat','Segoe Print',cursive;font-size:19px;opacity:.8;color:var(--accent)}}
.again[hidden]{{display:none}}
.qa.is-new,.slip.is-new,.tile.is-new{{position:relative}}
.qa.is-new::after,.slip.is-new::after,.tile.is-new::after{{content:'';position:absolute;top:-4px;right:-4px;width:9px;height:9px;border-radius:50%;background:var(--accent);box-shadow:0 0 0 3px rgba(var(--bg-rgb),.9);pointer-events:none}}
.sky{{position:fixed;inset:0;z-index:0;pointer-events:none;overflow:hidden;opacity:0;transition:opacity 1.2s}}
.sky i{{position:absolute;inset:-20% -10%;display:block;opacity:0}}
.sky--rain,.sky--snow,.sky--storm,.sky--fog,.sky--cloud,.sky--clear,.sky--night{{opacity:1}}
/* rain: three sheets of streaks, each falling at its own speed */
.sky--rain i,.sky--storm i{{opacity:.5;background-image:repeating-linear-gradient(101deg,transparent 0 26px,rgba(255,255,255,.45) 26px 27px);background-size:auto 240px;animation:sky-fall 1.05s linear infinite}}
.sky--rain i:nth-child(2),.sky--storm i:nth-child(2){{opacity:.3;background-size:auto 180px;animation-duration:1.5s;background-image:repeating-linear-gradient(99deg,transparent 0 41px,rgba(255,255,255,.4) 41px 42px)}}
.sky--rain i:nth-child(3),.sky--storm i:nth-child(3){{opacity:.18;background-size:auto 320px;animation-duration:.8s;background-image:repeating-linear-gradient(103deg,transparent 0 67px,rgba(255,255,255,.5) 67px 68px)}}
@keyframes sky-fall{{to{{background-position:60px 240px}}}}
/* storm adds a flash every so often */
.sky--storm{{animation:sky-flash 9s ease-out infinite}}
@keyframes sky-flash{{0%,92%,100%{{background:transparent}}93%{{background:rgba(255,255,255,.16)}}94%{{background:transparent}}95%{{background:rgba(255,255,255,.1)}}96%{{background:transparent}}}}
/* snow: three drifts of dots */
.sky--snow i{{opacity:.85;background-image:radial-gradient(2.6px 2.6px at 12% 6%,#fff,transparent),radial-gradient(2.2px 2.2px at 31% 17%,#fff,transparent),radial-gradient(2.6px 2.6px at 47% 9%,#fff,transparent),radial-gradient(2px 2px at 63% 24%,#fff,transparent),radial-gradient(2.4px 2.4px at 78% 13%,#fff,transparent),radial-gradient(2.8px 2.8px at 90% 30%,#fff,transparent),radial-gradient(2px 2px at 22% 34%,#fff,transparent),radial-gradient(2.4px 2.4px at 55% 41%,#fff,transparent),radial-gradient(2px 2px at 85% 46%,#fff,transparent);background-size:auto 380px;animation:sky-drift 11s linear infinite}}
.sky--snow i:nth-child(2){{opacity:.5;background-size:auto 300px;animation-duration:16s}}
.sky--snow i:nth-child(3){{opacity:.3;background-size:auto 560px;animation-duration:8s}}
@keyframes sky-drift{{to{{background-position:70px 380px}}}}
/* fog: two slow banks */
.sky--fog i{{opacity:.5;background:radial-gradient(60% 40% at 20% 70%,rgba(255,255,255,.18),transparent 70%),radial-gradient(70% 40% at 85% 40%,rgba(255,255,255,.12),transparent 70%);animation:sky-bank 26s ease-in-out infinite alternate}}
.sky--fog i:nth-child(2){{opacity:.35;animation-duration:38s;animation-direction:alternate-reverse}}
.sky--fog i:nth-child(3){{display:none}}
@keyframes sky-bank{{from{{transform:translate3d(-6%,2%,0)}}to{{transform:translate3d(6%,-2%,0)}}}}
/* cloud: one soft moving shadow, nothing more */
.sky--cloud i{{opacity:.28;background:radial-gradient(50% 30% at 30% 12%,rgba(255,255,255,.14),transparent 70%);animation:sky-bank 34s ease-in-out infinite alternate}}
.sky--cloud i:nth-child(2),.sky--cloud i:nth-child(3){{display:none}}
/* a clear night: a few slow stars */
.sky--night i{{opacity:.85;background-image:radial-gradient(1.8px 1.8px at 14% 11%,#fff,transparent),radial-gradient(1.5px 1.5px at 27% 22%,#fff,transparent),radial-gradient(2px 2px at 41% 7%,#fff,transparent),radial-gradient(1.4px 1.4px at 58% 16%,#fff,transparent),radial-gradient(1.9px 1.9px at 72% 27%,#fff,transparent),radial-gradient(1.5px 1.5px at 86% 12%,#fff,transparent),radial-gradient(1.7px 1.7px at 33% 37%,#fff,transparent),radial-gradient(1.4px 1.4px at 65% 44%,#fff,transparent),radial-gradient(1.8px 1.8px at 8% 58%,#fff,transparent),radial-gradient(1.5px 1.5px at 92% 63%,#fff,transparent),radial-gradient(1.6px 1.6px at 17% 76%,#fff,transparent),radial-gradient(2px 2px at 79% 82%,#fff,transparent),radial-gradient(1.4px 1.4px at 45% 91%,#fff,transparent),radial-gradient(1.7px 1.7px at 62% 69%,#fff,transparent);animation:sky-twinkle 6s ease-in-out infinite}}
.sky--night i:nth-child(2){{opacity:.35;animation-duration:9s;animation-delay:-3s}}
.sky--night i:nth-child(3){{display:none}}
@keyframes sky-twinkle{{0%,100%{{opacity:.25}}50%{{opacity:.7}}}}
/* a clear day: nothing but a warm wash */
.sky--clear i{{opacity:.18;background:radial-gradient(45% 30% at 78% 6%,rgba(255,236,190,.5),transparent 70%)}}
.sky--clear i:nth-child(2),.sky--clear i:nth-child(3){{display:none}}
.tag{{display:inline-flex;align-items:center;padding:3px 8px;border-radius:999px;font-size:10px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#1a1408;background:linear-gradient(135deg,#fff2c4,#E6C36B);box-shadow:0 0 18px -4px rgba(230,195,107,.8);vertical-align:middle;-webkit-text-fill-color:#1a1408;text-shadow:none}}
@property --ga{{syntax:'<angle>';inherits:false;initial-value:135deg}}
.card--gold{{border-width:1.5px;box-shadow:0 40px 100px -40px rgba(0,0,0,.9),0 0 70px -20px rgba(230,195,107,.55);animation:goldspin 7s linear infinite}}
@keyframes goldspin{{to{{--ga:495deg}}}}
.sparks{{position:fixed;inset:0;z-index:4;pointer-events:none}}
.bio--type .bio__caret{{display:inline-block;width:2px;height:1em;margin-left:2px;vertical-align:-.15em;background:var(--accent);animation:caret 1s steps(1) infinite}}
.bio--type.is-done .bio__caret{{animation-duration:1.6s}}
@keyframes caret{{50%{{opacity:0}}}}
.card.in-fade{{animation:in-fade .9s ease-out both}}
.card.in-rise{{animation:in-rise .8s cubic-bezier(.2,.8,.2,1) both}}
.card.in-flicker{{animation:in-flicker 1.3s steps(1) both}}
.card.in-glitch{{animation:in-glitch .9s steps(1) both}}
@keyframes in-fade{{from{{opacity:0}}}}
@keyframes in-rise{{from{{opacity:0;transform:translateY(28px)}}}}
@keyframes in-flicker{{0%,12%,22%,34%{{opacity:0}}6%,18%,28%{{opacity:.55}}40%{{opacity:1}}47%{{opacity:.3}}52%{{opacity:1}}}}
@keyframes in-glitch{{0%{{opacity:0;transform:translate(-8px,0);clip-path:inset(0 0 70% 0)}}15%{{opacity:1;transform:translate(6px,-2px);clip-path:inset(30% 0 40% 0);filter:drop-shadow(-4px 0 var(--accent))}}30%{{transform:translate(-4px,2px);clip-path:inset(60% 0 5% 0);filter:drop-shadow(4px 0 var(--accent))}}45%{{transform:translate(2px,0);clip-path:inset(10% 0 55% 0)}}60%{{transform:none;clip-path:inset(0);filter:none}}75%{{transform:translate(3px,-1px);filter:drop-shadow(-3px 0 var(--accent))}}85%{{transform:none;filter:none}}}}
@media (prefers-reduced-motion:reduce){{.bg-fx,.name--shimmer,.player__bars i,.entry__text,.bio__caret,.card,.card--gold,.player--vinyl .player__btn,.blk__dot,.avatar-wrap::before,.here__dot,.blk__colon{{animation:none!important}}.odo__col,.mood{{transition:none!important}}.blk--np .np__disc,.np__bars i{{animation:none!important}}.secret.in-glitch,.secret__ask.is-wrong input{{animation:none!important}}.bg-video{{display:none}}.sky i,.sky--storm{{animation:none!important}}.candle__flame,.draw__card{{animation:none!important}}.flip--on .card,.flip--on .card--back,.flip--on{{transition:none!important}}.candle.is-out .candle__flame,.candle.is-out{{transition:none!important}}.bio--type .bio__caret{{display:none}}}}
</style>
</head>
<body>
{SPRITE}
{video_tag}
<div class="bg-image" style="{image_style}" aria-hidden="true"></div>
<div class="bg-fx {fx_class}" aria-hidden="true"></div>
<div class="tint" aria-hidden="true"></div>
{'<div class="mood" data-mood aria-hidden="true"></div>' if mood_on else ''}
{sky_tag}
{flip_open}<main class="{card_classes}" tabindex="-1"{inert}{enter_attr}>
  {patina_tag}{seal_tag}{moon_tag}
  {avatar_tag}
  <h1 class="{name_classes}">{display_name}{'<span class="sr-only">, supporter</span><span class="tag" title="Supporter" aria-hidden="true">supporter</span>' if supporter_tag else ''}</h1>
  <p class="handle">misa.lol/{username}</p>
  {badges}
  {location_tag}{fresh_tag}
  {description_tag}
  {was_tag}{night_tag}{blocks_top}
  {socials}
  {again_tag}{blocks_bottom}
  {secret_tag}
  {capsule_tag}
  {draw_tag}
  {guestbook_tag}
  {asks_tag}
  {board_tag}
  {tally_tag}
  {vigil_tag}
  {nb_tag}
  {counter_tag}{here_tag}
  <div class="foot">{views_tag}{since_tag}{'' if hide_brand else '<a class="brand" href="/">made with <b>misa.lol</b></a>'}<button class="report" type="button" data-report-open aria-expanded="false" aria-controls="report-form">report</button></div>
  <form class="report-form" id="report-form" data-report-form hidden>
    <p class="report-form__t">report misa.lol/{username}</p>
    <select name="reason" aria-label="Reason"><option value="spam">spam</option><option value="impersonation">impersonation</option><option value="harassment">harassment</option><option value="illegal">illegal content</option><option value="other">something else</option></select>
    <textarea name="details" rows="3" maxlength="1000" placeholder="what's wrong? (optional)" aria-label="What's wrong? (optional)"></textarea>
    <div class="report-form__row"><button type="submit">send</button><button type="button" data-report-close>cancel</button></div>
    <p class="report-form__msg" data-report-msg role="status"></p>
  </form>
  {dogear_tag}
</main>{back_tag}{flip_close}
{audio_tag}
{entry_tag}
{'<canvas class="sparks" data-sparks aria-hidden="true"></canvas>' if sparkle_trail else ''}
<script>
(function(){{
  var p=document.querySelector('[data-player]'), a=p&&p.querySelector('audio'), b=p&&p.querySelector('[data-play]'), entry=document.querySelector('[data-entry]');
  var trackName=p?(p.querySelector('.player__name')||{{}}).textContent||'':'';
  function setPlaying(on){{ if(!p) return; p.classList.toggle('is-playing',on); b.setAttribute('aria-label',(on?'Pause ':'Play ')+trackName); b.querySelector('use').setAttribute('href',on?'#i-pause':'#i-play'); }}
  function play(){{ if(!a) return; a.volume={volume:.2f}; a.play().then(function(){{ setPlaying(true); }}).catch(function(){{ setPlaying(false); }}); }}
  if(b) b.addEventListener('click',function(){{ if(a.paused) play(); else {{ a.pause(); setPlaying(false); }} }});
  var reduce=matchMedia('(prefers-reduced-motion:reduce)').matches;
  /* v3.112: typewriter bio — the full text is in the sr-only span; this types the visible copy */
  var tw=document.querySelector('.bio--type');
  function typeBio(){{ if(!tw) return; var out=tw.querySelector('.bio__typed'), text=tw.getAttribute('data-type')||''; if(reduce){{ out.textContent=text; tw.classList.add('is-done'); return; }} var i=0; (function step(){{ out.textContent=text.slice(0,++i); if(i<text.length) setTimeout(step,text.charAt(i-1)==='.'?260:text.charAt(i-1)===' '?24:38); else tw.classList.add('is-done'); }})(); }}
  if(!entry) typeBio();
  /* v3.116: a tab title that moves — breathe (two titles trade places), scroll (the name walks), blink (a dot pulses) */
  var tabMode='{tab_title}'; if(tabMode&&!reduce){{ var base=document.title, nm='{display_name}'; var frames=tabMode==='breathe'?['\u2020 '+nm,nm+' \u00b7 misa.lol']:tabMode==='blink'?['\u25cf '+nm,'\u25cb '+nm]:null; var i=0, walk=nm+' \u00b7 misa.lol \u2020 ';
    setInterval(function(){{ if(frames){{ document.title=frames[i++%frames.length]; }} else {{ walk=walk.slice(1)+walk.charAt(0); document.title=walk; }} }},tabMode==='scroll'?400:tabMode==='blink'?900:2600); window.__tabTitle=function(){{ return document.title; }}; }}
  /* v3.113: sparkle trail — gold four-point sparks that follow the pointer; on touch screens a slow twinkle around the name */
  var sc=document.querySelector('[data-sparks]');
  if(sc&&!reduce){{ var cx=sc.getContext('2d'), sparks=[], raf=0, W=0, H=0, dpr=Math.min(devicePixelRatio||1,2);
    function size(){{ W=sc.width=innerWidth*dpr; H=sc.height=innerHeight*dpr; sc.style.width=innerWidth+'px'; sc.style.height=innerHeight+'px'; }} size(); addEventListener('resize',size);
    function spawn(x,y,n){{ for(var i=0;i<n;i++) sparks.push({{x:x*dpr+(Math.random()-.5)*14*dpr,y:y*dpr+(Math.random()-.5)*14*dpr,vx:(Math.random()-.5)*.6*dpr,vy:(-.4-Math.random()*.6)*dpr,r:(2+Math.random()*3.5)*dpr,life:1,rot:Math.random()*Math.PI,spin:(Math.random()-.5)*.1}}); if(sparks.length>90) sparks.splice(0,sparks.length-90); if(!raf) raf=requestAnimationFrame(tick); }}
    function tick(){{ cx.clearRect(0,0,W,H); for(var i=sparks.length-1;i>=0;i--){{ var s=sparks[i]; s.x+=s.vx; s.y+=s.vy; s.life-=.022; s.rot+=s.spin; if(s.life<=0){{ sparks.splice(i,1); continue; }} var r=s.r*(.4+s.life*.6); cx.save(); cx.translate(s.x,s.y); cx.rotate(s.rot); cx.globalAlpha=s.life; cx.fillStyle='#E6C36B'; cx.beginPath(); cx.moveTo(0,-r*2.2); cx.quadraticCurveTo(0,0,r*2.2,0); cx.quadraticCurveTo(0,0,0,r*2.2); cx.quadraticCurveTo(0,0,-r*2.2,0); cx.quadraticCurveTo(0,0,0,-r*2.2); cx.fill(); cx.globalAlpha=s.life*.6; cx.fillStyle='#fff2c4'; cx.beginPath(); cx.arc(0,0,r*.45,0,Math.PI*2); cx.fill(); cx.restore(); }} raf=sparks.length?requestAnimationFrame(tick):0; }}
    var lastT=0; addEventListener('pointermove',function(e){{ if(e.pointerType==='touch') return; var t=performance.now(); if(t-lastT<28) return; lastT=t; spawn(e.clientX,e.clientY,2); }},{{passive:true}});
    if(matchMedia('(hover:none)').matches){{ var nm=document.querySelector('.name'); setInterval(function(){{ if(!nm||document.hidden) return; var r=nm.getBoundingClientRect(); spawn(r.left+Math.random()*r.width,r.top+Math.random()*r.height,1); }},550); }}
    window.__sparks=function(){{ return sparks.length; }}; }}
  if(entry) entry.addEventListener('click',function(){{ entry.remove(); var m=document.querySelector('main'); if(p) p.removeAttribute('inert'); if(m){{ m.removeAttribute('inert'); if(m.dataset.enter) m.classList.add('in-'+m.dataset.enter); m.focus({{preventScroll:true}}); }} typeBio(); play(); var v=document.querySelector('.bg-video'); if(v&&v.play) v.play().catch(function(){{}}); }});
  else if(a&&{str(audio_enabled).lower()}) document.addEventListener('pointerdown',function once(e){{ if(e.target&&e.target.closest&&e.target.closest('[data-player]')) return; /* v3.114: a first tap on the play button itself used to start and then pause */ document.removeEventListener('pointerdown',once); if(a.paused) play(); }});
  /* v3.118: the hit counter rolls up from zero; the clock blocks tick; presence beats while the tab is open */
  var odo=document.querySelector('[data-odo]');
  if(odo&&!reduce){{ var cols=[].slice.call(odo.querySelectorAll('.odo__col')); cols.forEach(function(c){{ c.style.transition='none'; c.style.transform='translateY(0)'; }}); void odo.offsetHeight; requestAnimationFrame(function(){{ requestAnimationFrame(function(){{ cols.forEach(function(c){{ c.style.transition=''; c.style.transform=''; }}); }}); }}); }}
  var clocks=document.querySelectorAll('[data-clock]');
  function tickClocks(){{ for(var i=0;i<clocks.length;i++){{ var t=clocks[i]; try{{ var s=new Intl.DateTimeFormat('en-US',{{hour:'numeric',minute:'2-digit',timeZone:t.getAttribute('data-clock')}}).format(new Date()).toLowerCase(); t.innerHTML=s.replace(':','<span class="blk__colon">:</span>'); }}catch(e){{}} }} }}
  if(clocks.length){{ tickClocks(); setTimeout(function(){{ tickClocks(); setInterval(tickClocks,60000); }},60000-(Date.now()%60000)+200); window.__clock=function(){{ return clocks[0].textContent; }}; }}
  var hp=document.querySelector('[data-here]');
  if(hp){{ var ht=hp.querySelector('[data-here-text]'), hurl='/api/v1/presence/{username}', hTimer=0;
    function showHere(n){{ n=+n||0; if(n<1){{ hp.hidden=true; return; }} ht.textContent=n===1?'just you here right now':n.toLocaleString()+' people here right now'; hp.hidden=false; }}
    function beat(){{ if(document.hidden) return; fetch(hurl,{{method:'POST',credentials:'include',headers:{{Accept:'application/json'}}}}).then(function(r){{ return r.ok?r.json():null; }}).then(function(d){{ if(d&&'here' in d) showHere(d.here); }}).catch(function(){{}}); }}
    function schedule(){{ clearInterval(hTimer); hTimer=setInterval(beat,30000); }} schedule();
    document.addEventListener('visibilitychange',function(){{ if(!document.hidden){{ beat(); schedule(); }} }});
    addEventListener('pagehide',function(){{ if(navigator.sendBeacon) navigator.sendBeacon(hurl+'/leave'); }});
    window.__here=function(){{ return hp.hidden?0:+((ht.textContent.match(/[\\d,]+/)||['1'])[0].replace(/,/g,'')); }}; }}
  /* v3.125: the weather block — one poll when the render had nothing, then every ten minutes while the tab is open */
  var wxs=document.querySelectorAll('[data-wx]');
  if(wxs.length){{ function wxTick(){{ if(document.hidden) return; fetch('/api/v1/weather/{username}',{{headers:{{Accept:'application/json'}}}}).then(function(r){{ return r.ok?r.json():null; }}).then(function(d){{ if(!d||!d.line) return; for(var i=0;i<wxs.length;i++){{ var el=wxs[i]; el.querySelector('[data-wx-line]').textContent=d.line; el.querySelector('[data-wx-temp]').textContent=d.temp; var u=el.querySelector('use'); if(u&&d.icon) u.setAttribute('href','#i-'+d.icon); el.hidden=false; }} window.__wx=d; }}).catch(function(){{}}); }}
    setTimeout(wxTick,{'500' if any(isinstance(b, dict) and str(b.get("type") or "").lower() == "weather" and not (weather or {}).get(str(b.get("city") or "").strip()) for b in blocks_raw[:12]) else '600000'}); setInterval(wxTick,600000); }}
  /* v3.122: now playing — polls /api/v1/nowplaying/<name> every 45 s while the tab is open and swaps the line */
  var nps=document.querySelectorAll('[data-np]');
  if(nps.length){{ function npTick(){{ if(document.hidden) return; fetch('/api/v1/nowplaying/{username}',{{headers:{{Accept:'application/json'}}}}).then(function(r){{ return r.ok?r.json():null; }}).then(function(d){{ if(!d) return; for(var i=0;i<nps.length;i++){{ var el=nps[i], t=el.querySelector('[data-np-t]'), k=el.querySelector('[data-np-k]'); if(d.track){{ t.textContent=d.track+(d.artist?' \u2014 '+d.artist:''); k.textContent=d.playing?'now playing':'last played'+(d.ago?' \u00b7 '+d.ago:''); el.classList.toggle('is-live',!!d.playing); el.hidden=false; }} }} window.__np=d; }}).catch(function(){{}}); }}
    setTimeout(npTick,{'400' if any(isinstance(b, dict) and str(b.get("type") or "").lower() == "nowplaying" and b.get("lb") and not ((live or {}).get(str(b.get("lb") or "").strip()) or {}).get("track") for b in blocks_raw[:12]) else '45000'}); setInterval(npTick,45000); document.addEventListener('visibilitychange',function(){{ if(!document.hidden) npTick(); }}); }}
  /* v3.119: page moods — the wash follows the visitor's clock (dawn 5–8, day 9–16, dusk 17–20, night otherwise) */
  var moodEl=document.querySelector('[data-mood]');
  if(moodEl){{ function mood(){{ var h=new Date().getHours(); var m=h>=5&&h<9?'dawn':h>=9&&h<17?'day':h>=17&&h<21?'dusk':'night'; document.documentElement.setAttribute('data-mood',m); return m; }} mood(); setInterval(mood,60000); window.__mood=mood; }}
  /* v3.119: the secret word — typed anywhere (or said after five taps on the avatar); the word and the link never sit in this source */
  var sec=document.querySelector('[data-secret]'), ask=document.querySelector('[data-secret-ask]');
  if(sec&&ask&&window.crypto&&crypto.subtle){{ var need=+sec.getAttribute('data-n')||0, buf='', busy=false, found=false, taps=[];
    function hex(b){{ return Array.prototype.map.call(new Uint8Array(b),function(x){{ return ('0'+x.toString(16)).slice(-2); }}).join(''); }}
    function sha(bytes){{ return crypto.subtle.digest('SHA-256',bytes); }}
    function bytesOf(str){{ return new TextEncoder().encode(str); }}
    function unhex(h){{ var out=new Uint8Array(h.length/2); for(var i=0;i<out.length;i++) out[i]=parseInt(h.substr(i*2,2),16); return out; }}
    function reveal(word){{ found=true; sha(bytesOf(word)).then(function(key){{ var c=unhex(sec.getAttribute('data-c')), k=new Uint8Array(key), out=new Uint8Array(c.length), blocks=[]; for(var i=0;i<=(c.length>>5);i++){{ var b=new Uint8Array(33); b.set(k); b[32]=i; blocks.push(sha(b)); }}
      return Promise.all(blocks).then(function(bs){{ for(var j=0;j<c.length;j++) out[j]=c[j]^new Uint8Array(bs[j>>5])[j&31]; var url=new TextDecoder().decode(out); var a=sec.querySelector('[data-secret-link]'); a.href=url; ask.hidden=true; sec.hidden=false; sec.classList.add('in-glitch'); sec.scrollIntoView({{block:'nearest'}}); a.focus({{preventScroll:true}}); window.__secretUrl=url; }}); }}); }}
    function check(word){{ if(busy||found||word.length!==need) return Promise.resolve(false); busy=true; return sha(bytesOf('misa-secret|'+word)).then(function(d){{ busy=false; if(hex(d)===sec.getAttribute('data-v')){{ reveal(word); return true; }} return false; }}); }}
    document.addEventListener('keydown',function(e){{ if(found||e.ctrlKey||e.metaKey||e.altKey) return; var t=e.target; if(t&&(t.tagName==='INPUT'||t.tagName==='TEXTAREA'||t.tagName==='SELECT'||t.isContentEditable)) return; if(e.key.length!==1) return; buf=(buf+e.key.toLowerCase()).replace(/[^a-z0-9]/g,'').slice(-32); if(buf.length>=need) check(buf.slice(-need)); }});
    var av=document.querySelector('.avatar'); if(av) av.addEventListener('click',function(){{ var now=Date.now(); taps=taps.filter(function(t){{ return now-t<2500; }}); taps.push(now); if(taps.length>=5&&!found){{ taps=[]; ask.hidden=false; ask.querySelector('input').focus(); }} }});
    ask.addEventListener('submit',function(e){{ e.preventDefault(); var w=ask.querySelector('input').value.toLowerCase().replace(/[^a-z0-9]/g,''); check(w).then(function(ok){{ if(!ok){{ ask.classList.remove('is-wrong'); void ask.offsetWidth; ask.classList.add('is-wrong'); }} }}); }});
    ask.addEventListener('keydown',function(e){{ if(e.key==='Escape'){{ ask.hidden=true; }} }});
    window.__secretTry=check; }}
  /* v3.123: the chalkboard — a small canvas; strokes go to /api/v1/doodles/<name> as points in a 200×140 space */
  var bd=document.querySelector('[data-board-form]'), bo2=document.querySelector('[data-board-open]');
  if(bd&&bo2){{ var cv=bd.querySelector('[data-board-canvas]'), cx2=cv.getContext('2d'), strokes=[], cur=null, drawing2=false, chalking=false;
    function chalkColour(){{ var v=(bd.querySelector('input[name=colour]:checked')||{{}}).value||'chalk'; return {{chalk:'#EEE8E2',accent:getComputedStyle(document.documentElement).getPropertyValue('--accent').trim()||'#F00646',pink:'#ff9ac4',sky:'#7fd3ff',gold:'#E6C36B'}}[v]||'#EEE8E2'; }}
    function pt(e){{ var r=cv.getBoundingClientRect(); return [Math.max(0,Math.min(200,Math.round((e.clientX-r.left)/r.width*200))),Math.max(0,Math.min(140,Math.round((e.clientY-r.top)/r.height*140)))]; }}
    function repaint(){{ cx2.clearRect(0,0,cv.width,cv.height); cx2.lineCap='round'; cx2.lineJoin='round'; cx2.lineWidth=6.4; strokes.forEach(function(st){{ cx2.strokeStyle=st.colour; cx2.fillStyle=st.colour; var p=st.p; if(p.length===2){{ cx2.beginPath(); cx2.arc(p[0]*2,p[1]*2,4,0,Math.PI*2); cx2.fill(); return; }} cx2.beginPath(); cx2.moveTo(p[0]*2,p[1]*2); for(var i=2;i<p.length;i+=2) cx2.lineTo(p[i]*2,p[i+1]*2); cx2.stroke(); }}); }}
    cv.addEventListener('pointerdown',function(e){{ if(strokes.length>=40) return; e.preventDefault(); cv.setPointerCapture(e.pointerId); drawing2=true; var q=pt(e); cur={{colour:chalkColour(),p:[q[0],q[1]]}}; strokes.push(cur); repaint(); }});
    cv.addEventListener('pointermove',function(e){{ if(!drawing2||!cur) return; var q=pt(e), p=cur.p; if(Math.abs(p[p.length-2]-q[0])<1&&Math.abs(p[p.length-1]-q[1])<1) return; if(p.length<800){{ p.push(q[0],q[1]); repaint(); }} }});
    function up(){{ drawing2=false; cur=null; }} cv.addEventListener('pointerup',up); cv.addEventListener('pointercancel',up); cv.addEventListener('lostpointercapture',up);
    function closeBoard(){{ bd.hidden=true; bo2.setAttribute('aria-expanded','false'); bo2.focus(); }}
    bo2.addEventListener('click',function(){{ if(!bd.hidden){{ closeBoard(); return; }} bd.hidden=false; bo2.setAttribute('aria-expanded','true'); cv.focus(); }});
    bd.querySelector('[data-board-close]').addEventListener('click',closeBoard);
    bd.querySelector('[data-board-clear]').addEventListener('click',function(){{ strokes=[]; repaint(); }});
    bd.addEventListener('keydown',function(e){{ if(e.key==='Escape') closeBoard(); }});
    bd.addEventListener('submit',function(e){{ e.preventDefault(); var m=bd.querySelector('[data-board-msg]'), sb=bd.querySelector('[type=submit]'); if(chalking) return; if(!strokes.length){{ m.textContent='draw something first.'; return; }} chalking=true; sb.setAttribute('aria-busy','true');
      fetch('/api/v1/doodles/{username}',{{method:'POST',credentials:'include',headers:{{'Content-Type':'application/json',Accept:'application/json'}},body:JSON.stringify({{strokes:strokes.map(function(s){{ return s.p; }}),colour:(bd.querySelector('input[name=colour]:checked')||{{}}).value||'chalk'}})}})
        .then(function(r){{ return r.json().catch(function(){{ return {{}}; }}).then(function(d){{ m.textContent=r.ok?(d.message||'chalked.'):(typeof d.detail==='string'?d.detail:'could not leave that.'); if(r.ok){{ strokes=[]; repaint(); setTimeout(function(){{ closeBoard(); m.textContent=''; }},2600); }} }}); }})
        .catch(function(){{ m.textContent='could not leave that.'; }}).then(function(){{ chalking=false; sb.removeAttribute('aria-busy'); }}); }});
    window.__board=function(){{ return strokes.map(function(s){{ return s.p.length/2; }}); }}; }}
  /* v3.117: the guestbook form → /api/v1/guestbook/<name> */
  var bf=document.querySelector('[data-book-form]'), bo=document.querySelector('[data-book-open]');
  if(bf&&bo){{ var signing=false; function closeBook(){{ bf.hidden=true; bo.setAttribute('aria-expanded','false'); bo.focus(); }}
    bo.addEventListener('click',function(){{ if(!bf.hidden){{ closeBook(); return; }} bf.hidden=false; bo.setAttribute('aria-expanded','true'); bf.querySelector('input').focus(); }});
    bf.querySelector('[data-book-close]').addEventListener('click',closeBook);
    bf.addEventListener('keydown',function(e){{ if(e.key==='Escape') closeBook(); }});
    bf.addEventListener('submit',function(e){{ e.preventDefault(); if(signing) return; var m=bf.querySelector('[data-book-msg]'), sb=bf.querySelector('[type=submit]'); signing=true; sb.setAttribute('aria-busy','true');
      fetch('/api/v1/guestbook/{username}',{{method:'POST',credentials:'include',headers:{{'Content-Type':'application/json',Accept:'application/json'}},body:JSON.stringify({{name:bf.name.value,line:bf.line.value}})}})
        .then(function(r){{ return r.json().catch(function(){{ return {{}}; }}).then(function(d){{ m.textContent=r.ok?(d.message||'signed.'):(typeof d.detail==='string'?d.detail:'could not sign that.'); if(r.ok){{ bf.name.value=''; bf.line.value=''; setTimeout(function(){{ closeBook(); m.textContent=''; }},2600); }} }}); }})
        .catch(function(){{ m.textContent='could not sign that.'; }}).then(function(){{ signing=false; sb.removeAttribute('aria-busy'); }}); }}); }}
  /* v3.132: the page remembers you — entirely in your browser. Nothing is sent anywhere, and clearing site data forgets it.
     A visit counts once every half hour, the same window the view counter uses. */
  var againEl=document.querySelector('[data-again]');
  if(againEl){{
    var KEY='misa:seen:{username}', MON=['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'];
    var now=Date.now(), was=null;
    try{{ was=JSON.parse(localStorage.getItem(KEY)||'null'); }}catch(e){{ was=null; }}
    if(!was||typeof was!=='object'||!was.n) was={{n:0,first:now,last:0}};
    var fresh=(now-(was.last||0))>1800000;                       /* a refresh is not another visit */
    var visits=was.n+(fresh?1:0);
    var line='';
    if(visits>1){{
      var since=now-(was.last||now), d=new Date(was.last||now);
      if(since>3888000000) line='long time. you were last here in '+MON[d.getMonth()]+(d.getFullYear()!==new Date().getFullYear()?' '+d.getFullYear():'')+'.';
      else if(visits===2) line='you’ve been here before.';
      else if(visits<10) line='that’s '+visits+' visits.';
      else line='you’re a regular here.';
    }}
    /* v3.133: what arrived while they were away. Every answer, signature and drawing carries the second it
       appeared; their browser compares it with the last visit it remembers. Nobody is told what they saw. */
    var newBits=[];
    if(visits>1&&was.last){{
      var kinds=[['.qa','answer','answers'],['.slip','signature','signatures'],['.wall .tile','drawing','drawings']];
      for(var ki=0;ki<kinds.length;ki++){{
        var els=[].slice.call(document.querySelectorAll(kinds[ki][0])), fresh2=[];
        for(var ei=0;ei<els.length;ei++){{ var at=+els[ei].getAttribute('data-at')||0; if(at*1000>was.last) fresh2.push(els[ei]); }}
        if(fresh2.length){{ newBits.push(fresh2.length+' new '+(fresh2.length===1?kinds[ki][1]:kinds[ki][2])); for(var fi=0;fi<fresh2.length;fi++) fresh2[fi].classList.add('is-new'); }}
      }}
    }}
    if(line&&newBits.length) line+=' '+newBits.join(', ')+' since.';
    if(line){{ againEl.textContent=line; againEl.hidden=false; }}
    try{{ localStorage.setItem(KEY,JSON.stringify({{n:visits,first:was.first||now,last:fresh?now:(was.last||now)}})); }}catch(e){{}}
    window.__again=function(){{ return againEl.hidden?'':againEl.textContent; }};
  }}
  /* v3.130: the sky — the state the server rendered, kept current by the same weather the page already asks for */
  var skyEl=document.querySelector('[data-sky]');
  if(skyEl){{ var SKY_STATES=['rain','snow','storm','fog','cloud','clear','night'];
    window.__sky=function(){{ return (skyEl.className.match(/sky--([a-z]+)/)||[,''])[1]; }};
    window.__setSky=function(state){{ if(SKY_STATES.indexOf(state)<0) return; SKY_STATES.forEach(function(x){{ skyEl.classList.remove('sky--'+x); }}); skyEl.classList.add('sky--'+state); }};
    function skyPoll(){{ fetch('/api/v1/weather/{username}',{{headers:{{Accept:'application/json'}}}}).then(function(r){{ return r.ok?r.json():null; }})
      .then(function(d){{ if(d&&d.sky) window.__setSky(d.sky); }}).catch(function(){{}}).then(function(){{ setTimeout(skyPoll,600000); }}); }}
    setTimeout(skyPoll, skyEl.className.indexOf('sky--')<0?800:600000); }}
  /* v3.129: the capsule counts down to the day it opens. The words are not here — the server sends them only once it's time. */
  var cap=document.querySelector('[data-capsule]');
  if(cap){{ var left=cap.querySelector('[data-capsule-left]'), when=Date.parse(cap.getAttribute('data-capsule'));
    function capTick(){{ var d=Math.max(0,when-Date.now());
      if(!d){{ left.textContent='opening — refresh the page'; return; }}
      var days=Math.floor(d/86400000), hrs=Math.floor(d/3600000)%24, mins=Math.floor(d/60000)%60;
      left.textContent=days>0?(days+(days===1?' day':' days')+', '+hrs+'h to go'):(hrs>0?(hrs+'h '+mins+'m to go'):(mins+(mins===1?' minute':' minutes')+' to go'));
      setTimeout(capTick,60000-Date.now()%60000); }}
    capTick(); window.__capsule=function(){{ return left.textContent; }}; }}
  /* v3.128: the ask box → /api/v1/asks/<name>. An answer only ever appears once the owner writes one. */
  var af=document.querySelector('[data-ask-form]');
  if(af){{ var asking=false;
    af.addEventListener('submit',function(e){{ e.preventDefault(); if(asking) return; var m=af.querySelector('[data-ask-msg]'), sb=af.querySelector('[type=submit]'), q=af.question.value.trim();
      if(!q) return; asking=true; sb.setAttribute('aria-busy','true');
      fetch('/api/v1/asks/{username}',{{method:'POST',credentials:'include',headers:{{'Content-Type':'application/json',Accept:'application/json'}},body:JSON.stringify({{question:q}})}})
        .then(function(r){{ return r.json().catch(function(){{ return {{}}; }}).then(function(d){{ m.textContent=r.ok?(d.message||'asked.'):(typeof d.detail==='string'?d.detail:'could not ask that.'); if(r.ok) af.question.value=''; }}); }})
        .catch(function(){{ m.textContent='could not ask that.'; }}).then(function(){{ asking=false; sb.removeAttribute('aria-busy'); }}); }});
    window.__ask=function(v){{ af.question.value=v; af.dispatchEvent(new Event('submit',{{cancelable:true}})); }}; }}
  /* v3.144: neighbours — the render used whatever was cached; this asks for a fresh answer, which is what
     keeps a page from doing five lookups while somebody is waiting for it. */
  var nb=document.querySelector('[data-neighbours]');
  if(nb){{ fetch('/api/v1/neighbours/{username}',{{headers:{{Accept:'application/json'}}}}).then(function(r){{ return r.ok?r.json():null; }})
    .then(function(d){{ if(!d||!d.neighbours) return; var list=nb.querySelector('[data-nb-list]'), empty=nb.querySelector('[data-nb-empty]');
      if(!d.neighbours.length){{ list.innerHTML=''; if(!empty){{ var p=document.createElement('p'); p.className='nb__empty'; p.setAttribute('data-nb-empty',''); p.textContent='nobody has named this page back yet.'; nb.appendChild(p); }} return; }}
      if(empty) empty.remove();
      list.innerHTML=d.neighbours.map(function(n){{
        var a=document.createElement('a'); a.href='/'+n.username; if(n.accent) a.style.setProperty('--nb',n.accent);
        a.innerHTML='<span class="nb__dot" aria-hidden="true"></span>';
        a.appendChild(document.createTextNode(String(n.name||n.username).slice(0,40)));
        var s=document.createElement('small'); s.textContent='misa.lol/'+n.username; a.appendChild(s);
        var li=document.createElement('li'); li.className='nb__one'; li.appendChild(a); return li.outerHTML; }}).join(''); }})
    .catch(function(){{}});
    window.__nb=function(){{ return [].map.call(nb.querySelectorAll('.nb__one a'),function(a){{ return a.getAttribute('href'); }}); }}; }}
  /* v3.136: the tally. The counts are public, so the page reads them; which one you picked is yours, and stays
     in your own browser (same shelf as the “you've been here before” line — nothing about it is sent anywhere). */
  var tal=document.querySelector('[data-tally]');
  if(tal){{ var qid=tal.getAttribute('data-tally'), tkey='misa:tally:{username}:'+qid, mine=null, voting=false;
    try{{ var v=localStorage.getItem(tkey); if(v!==null) mine=+v; }}catch(e){{}}
    function tmarks(n){{ var out='', left=Math.min(n,25);
      while(left>0){{ var five=Math.min(5,left); left-=five; out+='<b class="mark'+(five===5?' mark--five':'')+'">'+new Array(Math.min(4,five)+1).join('<i></i>')+'</b>'; }}
      return out; }}
    function paint(counts){{
      tal.classList.toggle('is-done',mine!==null);
      tal.querySelectorAll('[data-tal-pick]').forEach(function(b){{ b.disabled=mine!==null; }});
      if(!counts) return;
      counts.forEach(function(n,i){{ var m=tal.querySelector('[data-tal-marks="'+i+'"]'), c=tal.querySelector('[data-tal-n="'+i+'"]'), row=tal.querySelector('[data-tal-row="'+i+'"]');
        if(m) m.innerHTML=tmarks(+n||0); if(c) c.textContent=(+n||0)?String(n):'';
        if(row) row.classList.toggle('is-mine',mine===i); }}); }}
    function tread(){{ fetch('/api/v1/tally/{username}',{{headers:{{Accept:'application/json'}}}}).then(function(r){{ return r.ok?r.json():null; }})
      .then(function(d){{ if(d&&d.counts) paint(d.counts); }}).catch(function(){{}}); }}
    tal.addEventListener('click',function(e){{ var b=e.target.closest&&e.target.closest('[data-tal-pick]'); if(!b||voting||mine!==null) return;
      var pick=+b.getAttribute('data-tal-pick'); voting=true; var msg=tal.querySelector('[data-tal-msg]');
      fetch('/api/v1/tally/{username}',{{method:'POST',headers:{{'Content-Type':'application/json',Accept:'application/json'}},body:JSON.stringify({{choice:pick}})}})
        .then(function(r){{ return r.json().catch(function(){{ return {{}}; }}).then(function(d){{
          if(r.ok){{ mine=pick; try{{ localStorage.setItem(tkey,String(pick)); }}catch(e){{}} paint(d.counts); }}
          else {{ if(r.status===429){{ mine=-1; paint(null); tread(); }} if(msg) msg.textContent=typeof d.detail==='string'?d.detail:'could not count that.'; }} }}); }})
        .catch(function(){{ if(msg) msg.textContent='could not count that.'; }}).then(function(){{ voting=false; }}); }});
    tread();
    window.__tally=function(){{ return {{mine:mine,marks:[].map.call(tal.querySelectorAll('[data-tal-marks]'),function(m){{ return m.querySelectorAll('.mark i').length; }}),
      n:[].map.call(tal.querySelectorAll('[data-tal-n]'),function(c){{ return c.textContent; }}),done:tal.classList.contains('is-done')}}; }}; }}
  /* v3.135: the back of the page. Without this the two faces just stack and everything is readable; with it,
     they become one card that turns over. The hidden face is inert, so Tab never wanders round the back. */
  var flip=document.querySelector('[data-flip]');
  if(flip){{ var front=flip.querySelector('.card'), back=flip.querySelector('[data-card-back]'), opener=flip.querySelector('[data-flip-to="back"]');
    flip.classList.add('flip--on');
    function fit(){{ var el=flip.classList.contains('is-back')?back:front; flip.style.height=el.offsetHeight+'px'; }}
    function face(showBack){{ flip.classList.toggle('is-back',showBack); fit();
      (showBack?front:back).setAttribute('inert','');  (showBack?back:front).removeAttribute('inert');
      (showBack?front:back).setAttribute('aria-hidden','true'); (showBack?back:front).removeAttribute('aria-hidden');
      if(opener) opener.setAttribute('aria-expanded',showBack?'true':'false'); }}
    face(false);
    addEventListener('resize',fit); addEventListener('load',fit); setTimeout(fit,400); setTimeout(fit,1600);
    flip.addEventListener('click',function(e){{ var b=e.target.closest&&e.target.closest('[data-flip-to]'); if(!b) return;
      var showBack=b.getAttribute('data-flip-to')==='back'; face(showBack);
      var land=showBack?back.querySelector('.back__title'):front.querySelector('.name');
      if(land){{ land.setAttribute('tabindex','-1'); land.focus({{preventScroll:true}}); }} }});
    addEventListener('keydown',function(e){{ if(e.key==='Escape'&&flip.classList.contains('is-back')) face(false); }});
    window.__flip=function(){{ return flip.classList.contains('is-back')?'back':'front'; }}; }}
  /* v3.134: the vigil — the shelf burns down here, in the page, from what the server said was left at render */
  var shelf=document.querySelector('[data-shelf]'), vb=document.querySelector('[data-vigil-light]');
  if(shelf){{ var t0=Date.now(), vburn={vigil_burn or 0}, lastPull=Date.now();
    function noteEl(){{ return document.querySelector('[data-vigil-note]'); }}
    function saySome(n){{ var el=noteEl(); if(!el) return; var hrs=Math.round(vburn/3600);
      if(n){{ el.className='vigil__note'; el.textContent=n+' candle'+(n===1?'':'s')+' burning \u00b7 they go out after '+hrs+' hours'; }}
      else {{ el.className='vigil__empty'; el.textContent='the shelf is dark. nobody has lit one in '+hrs+' hours.'; }} }}
    function burnDown(){{ var gone=(Date.now()-t0)/1000, alive=0;
      [].forEach.call(shelf.children,function(c){{ var left=(+c.getAttribute('data-left')||0)-gone, burn=+c.getAttribute('data-burn')||vburn;
        if(left<=0){{ if(!c.classList.contains('is-out')){{ c.classList.add('is-out'); setTimeout(function(){{ if(c.parentNode) c.parentNode.removeChild(c); saySome(shelf.children.length); }},900); }} return; }}
        alive++; c.style.setProperty('--h',Math.max(0,Math.min(1,left/burn)).toFixed(3)); }});
      return alive; }}
    function draw(list){{ shelf.innerHTML=''; t0=Date.now();
      (list||[]).forEach(function(c){{ var li=document.createElement('li'); li.className='candle';
        li.setAttribute('data-left',c.left); li.setAttribute('data-burn',c.burn); li.style.setProperty('--h',Math.max(0,Math.min(1,c.left/c.burn)).toFixed(3));
        li.innerHTML='<i class="candle__flame" aria-hidden="true"></i><b class="candle__wax"></b><u class="candle__pool"></u>'; shelf.appendChild(li); }});
      saySome(shelf.children.length); }}
    burnDown(); setInterval(burnDown,20000);
    if(vb) vb.addEventListener('click',function(){{ if(vb.disabled) return; var m=document.querySelector('[data-vigil-msg]'); vb.disabled=true;
      fetch('/api/v1/vigil/{username}',{{method:'POST',credentials:'include',headers:{{Accept:'application/json'}}}})
        .then(function(r){{ return r.json().catch(function(){{ return {{}}; }}).then(function(d){{
          if(r.ok){{ draw(d.lit); lastPull=Date.now(); if(m) m.textContent=d.message||'lit.'; vb.textContent='yours is burning'; }}
          else {{ if(m) m.textContent=typeof d.detail==='string'?d.detail:'could not light one.'; vb.disabled=false; }} }}); }})
        .catch(function(){{ if(m) m.textContent='could not light one.'; vb.disabled=false; }}); }});
    document.addEventListener('visibilitychange',function(){{ if(document.hidden||Date.now()-lastPull<120000) return; lastPull=Date.now();
      fetch('/api/v1/vigil/{username}',{{headers:{{Accept:'application/json'}}}}).then(function(r){{ return r.ok?r.json():null; }})
        .then(function(d){{ if(d&&d.lit) draw(d.lit); }}).catch(function(){{}}); }});
    window.__vigil=function(){{ return {{lit:shelf.children.length,alive:burnDown(),note:(noteEl()||{{}}).textContent||''}}; }}; }}
  /* report this page → /api/v1/reports */
  var rf=document.querySelector('[data-report-form]'), ro=document.querySelector('[data-report-open]');
  var sending=false;
  function closeReport(){{ rf.hidden=true; ro.setAttribute('aria-expanded','false'); ro.focus(); }}
  if(rf&&ro){{ ro.addEventListener('click',function(){{ if(!rf.hidden){{ closeReport(); return; }} rf.hidden=false; ro.setAttribute('aria-expanded','true'); rf.querySelector('select').focus(); }});
    rf.querySelector('[data-report-close]').addEventListener('click',closeReport);
    rf.addEventListener('keydown',function(e){{ if(e.key==='Escape') closeReport(); }});
    rf.addEventListener('submit',function(e){{ e.preventDefault(); if(sending) return; var m=rf.querySelector('[data-report-msg]'), b=rf.querySelector('[type=submit]'); sending=true; b.setAttribute('aria-busy','true');
      fetch('/api/v1/reports',{{method:'POST',credentials:'include',headers:{{'Content-Type':'application/json',Accept:'application/json'}},body:JSON.stringify({{username:'{username}',reason:rf.reason.value,details:rf.details.value}})}})
        .then(function(r){{ return r.json().catch(function(){{ return {{}}; }}).then(function(d){{ m.textContent=r.ok?(d.message||'Thanks.'):(typeof d.detail==='string'?d.detail:'Could not send that.'); if(r.ok) setTimeout(function(){{ closeReport(); m.textContent=''; }},2200); }}); }})
        .catch(function(){{ m.textContent='Could not send that.'; }}).then(function(){{ sending=false; b.removeAttribute('aria-busy'); }}); }}); }}
  /* link clicks → the owner's analytics (a beacon, never blocks the navigation) */
  document.addEventListener('click',function(e){{ var l=e.target&&e.target.closest&&e.target.closest('a[data-go]'); if(l&&navigator.sendBeacon) navigator.sendBeacon('/api/v1/hit/{username}/'+encodeURIComponent(l.getAttribute('data-go'))); }});
}})();
</script>
</body>
</html>"""
