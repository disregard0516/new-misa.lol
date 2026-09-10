"""Plan gating for profile configs (v3.5).

What each plan includes follows the pricing compare table on the site; edit GATES to change it.
Free pages get the basics; the paid-only cosmetics are cleared server-side on save so the dashboard
can't be talked into them. Badges never come from the request at all (see api/v1/profile.py).
"""
from typing import Any

PLAN_RANK = {"free": 0, "lifetime": 1, "supporter": 2}

# dotted path in the profile config → minimum plan rank, and the value it falls back to
GATES: list[tuple[str, int, Any]] = [
    ("assets.backgroundVideo.url", 1, None),   # video backgrounds — Lifetime and up
    ("settings.backgroundEffect", 1, "None"),  # animated backgrounds — Lifetime and up
    ("settings.usernameEffect", 1, "None"),    # username effects — Lifetime and up
    ("settings.entryScreen", 1, False),        # entrance animations — Lifetime and up
    ("settings.bioTypewriter", 1, False),      # typewriter bio — Lifetime and up (v3.112)
    ("settings.entryAnimation", 1, "None"),    # entrance animations — Lifetime and up (v3.112)
    ("settings.hideBrand", 1, False),          # footer badge off — Lifetime and up (v3.112)
    ("assets.cursor.url", 2, None),            # cursors — Supporter only
    ("settings.cursor", 2, "default"),         # the built-in gold star / ring / snow cursors — Supporter only (v3.112)
    ("settings.supporterTag", 2, False),       # the Supporter tag by the name (v3.113)
    ("settings.sparkleTrail", 2, False),       # gold sparks that trail the pointer (v3.113)
    ("settings.goldBorder", 2, False),         # the animated gold profile border (v3.113)
    ("settings.font", 1, "inter"),             # page fonts — Lifetime and up; two are Supporter-only, see SUPPORTER_FONTS (v3.114)
    ("settings.playerStyle", 1, "bars"),       # music-player styles — Lifetime and up (v3.114)
    ("settings.blocks", 1, []),                # content blocks — Lifetime and up (v3.115)
    ("settings.shareCard", 1, None),           # the custom share card — Lifetime and up (v3.115)
    ("settings.avatarFrame", 1, "none"),       # avatar frames — Lifetime and up (v3.116); link styles are for everyone
    ("settings.tabTitle", 1, "none"),          # the moving tab title — Lifetime and up (v3.116)
    ("settings.counterStyle", 1, "plain"),     # odometer / lcd / flip hit counters — Lifetime and up (v3.118); presence is for everyone
    ("settings.mood", 1, False),               # page moods by the visitor's hour — Lifetime and up (v3.119)
    ("settings.secret", 1, None),              # the secret word + hidden link — Lifetime and up (v3.119)
    ("settings.capsule", 1, None),            # the time capsule — Lifetime and up (v3.129)
    ("settings.sky", 1, None),                # real weather drawn over the page — Lifetime and up (v3.130)
    ("settings.reverse", 1, None),            # the back of the page — Lifetime and up (v3.135)
    ("settings.draw", 1, None),               # a line dealt to each visitor — Lifetime and up (v3.138)
    ("settings.night", 1, None),              # the night shift — Lifetime and up (v3.142)
    ("settings.usernameGlow", 2, False),       # gold glow / halo — Supporter only
]


def plan_rank(plan: str | None) -> int:
    return PLAN_RANK.get((plan or "free").strip().lower(), 1)


def _get(obj: dict[str, Any], path: str) -> Any:
    cur: Any = obj
    for key in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _set(obj: dict[str, Any], path: str, value: Any) -> None:
    keys = path.split(".")
    cur = obj
    for key in keys[:-1]:
        nxt = cur.get(key)
        if not isinstance(nxt, dict):
            return  # nothing to clear
        cur = nxt
    if keys[-1] in cur:
        cur[keys[-1]] = value


SUPPORTER_FONTS = {"unifraktur", "cormorant"}  # the exclusive fonts (mirrors app/profile_page.py)


def gate_profile(profile: dict[str, Any], plan: str | None) -> list[str]:
    """Clear paid-only fields the plan doesn't cover. Returns the paths that were cleared."""
    rank = plan_rank(plan)
    cleared: list[str] = []
    for path, needed, fallback in GATES:
        if rank < needed and _get(profile, path) not in (None, fallback, "", "None", False):
            _set(profile, path, fallback)
            cleared.append(path)
    if rank < 2 and str(_get(profile, "settings.font") or "").lower() in SUPPORTER_FONTS:
        _set(profile, "settings.font", "inter")
        if "settings.font" not in cleared:
            cleared.append("settings.font")
    return cleared
