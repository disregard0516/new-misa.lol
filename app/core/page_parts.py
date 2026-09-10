"""What a public page needs besides its own config (v3.137).

`render_public_profile` is a pure function: a config in, the page out. Everything else it draws — the
signatures on the guestbook, the answered questions, the drawings, the candles still lit, the sky over the
owner's town — is read separately and handed to it. This gathers those, so the live page and the dashboard's
*see your page* preview draw exactly the same things from exactly the same code.

Nothing here writes: no view is counted, no presence beaten, nothing noted in the replay. Both callers do
their own counting, because only one of them should.
"""
from __future__ import annotations

from typing import Any


async def gather(user_id: str, profile: dict[str, Any], visitor: str = "") -> dict[str, Any]:
    """The keyword arguments `render_public_profile` takes beyond the config itself. Never raises.

    `visitor` is the short salted hash of whoever is looking, when there is one — only the draw uses it, to
    deal them their line for the day. It is never stored, and an empty one just deals a steady line.
    """
    settings = (profile or {}).get("settings") or {}
    blocks = [b for b in (settings.get("blocks") or [])[:12] if isinstance(b, dict) and b.get("enabled") is not False]
    out: dict[str, Any] = {}

    if settings.get("guestbook"):
        try:
            from app.core.guestbook import approved as approved_signatures
            out["signatures"] = await approved_signatures(user_id)
        except Exception:
            out["signatures"] = []
    if settings.get("doodles"):
        try:
            from app.core.doodles import approved as approved_drawings
            out["drawings"] = await approved_drawings(user_id)
        except Exception:
            out["drawings"] = []
    if settings.get("asks"):
        try:
            from app.core.asks import answered as answered_asks
            out["asked"] = await answered_asks(user_id)
        except Exception:
            out["asked"] = []
    if settings.get("vigil"):
        try:
            from app.core.vigil import lit as lit_candles
            out["candles"] = await lit_candles(user_id)
        except Exception:
            out["candles"] = []

    if settings.get("draw"):  # v3.138: the line this visitor gets today — worked out here, never stored
        try:
            from app.core.draw import clean as draw_clean, pick as draw_pick
            deck = draw_clean(settings.get("draw"))
            if deck:
                out["drawn"] = draw_pick(deck, visitor or "someone")
        except Exception:
            pass

    if settings.get("neighbours"):  # v3.144: whatever has resolved already — never a lookup on the render path
        try:
            from app.core.neighbours import peek as nb_peek
            got = await nb_peek(user_id)
            if got:
                out["neighbours"] = got
        except Exception:
            pass

    try:  # now-playing blocks — the cache, never the network, on a page render
        from app.core.nowplaying import clean_user, peek
        names = {clean_user(b.get("lb")) for b in blocks if str(b.get("type") or "").lower() == "nowplaying"}
        names.discard("")
        if names:
            out["live"] = {n: await peek(n) for n in names}
    except Exception:
        pass
    try:  # weather blocks — likewise
        from app.core.weather import clean_place, peek as wx_peek
        places = {clean_place(b.get("city")) for b in blocks if str(b.get("type") or "").lower() == "weather"}
        places.discard("")
        if places:
            out["weather"] = {pl: await wx_peek(pl) for pl in places}
    except Exception:
        pass
    if str(settings.get("sky") or "").strip():  # the real weather over the page — cache only
        try:
            from app.core.weather import clean_place as sky_place, effect as sky_effect, peek as sky_peek
            place = sky_place(str(settings.get("sky")))
            data = await sky_peek(place) if place else None
            if data:
                out["sky"] = sky_effect(int(data.get("code", 3)), bool(data.get("day", True)))
        except Exception:
            pass
    return out
