"""v3.112 — the Lifetime set the pages promised: typewriter bio, entrance animations, the footer badge off, and the built-in
Supporter cursors. Each one renders on the public page, and each one is cleared for a plan that doesn't cover it."""
from app.core.plans import gate_profile
from app.profile_page import BUILTIN_CURSORS, render_public_profile


def _cfg(settings=None, assets=None, description="graveyard shift. berlin, mostly.", socials=None):
    return {
        "profile": {"username": "ren", "displayName": "ren", "description": description},
        "settings": settings or {},
        "assets": assets or {},
        "socials": socials or [],
        "badges": [],
    }


def test_typewriter_bio_keeps_the_full_text_for_screen_readers():
    html = render_public_profile(_cfg({"bioTypewriter": True}))
    assert 'class="bio bio--type" data-type="graveyard shift. berlin, mostly."' in html
    assert '<span class="sr-only">graveyard shift. berlin, mostly.</span>' in html
    assert "typeBio()" in html
    plain = render_public_profile(_cfg({"bioTypewriter": False}))
    assert '<p class="bio">graveyard shift. berlin, mostly.</p>' in plain and 'class="bio bio--type"' not in plain
    # no bio, no typewriter markup
    assert 'class="bio bio--type"' not in render_public_profile(_cfg({"bioTypewriter": True}, description=""))


def test_typewriter_text_is_escaped_in_the_attribute():
    html = render_public_profile(_cfg({"bioTypewriter": True}, description='a "quoted" <bio>'))
    assert 'data-type="a &quot;quoted&quot; &lt;bio&gt;"' in html
    assert "<bio>" not in html


def test_entrance_animation_on_the_card_or_after_the_entry_screen():
    for name in ("Fade", "Rise", "Flicker", "Glitch"):
        html = render_public_profile(_cfg({"entryAnimation": name}))
        assert f'<main class="card in-{name.lower()}" tabindex="-1">' in html
        assert f"@keyframes in-{name.lower()}" in html
    # with the entry screen on, the animation waits for the click
    html = render_public_profile(_cfg({"entryAnimation": "Rise", "entryScreen": True}))
    assert '<main class="card" tabindex="-1" inert data-enter="rise">' in html
    assert "m.classList.add('in-'+m.dataset.enter)" in html
    # unknown names do nothing
    assert '<main class="card" tabindex="-1">' in render_public_profile(_cfg({"entryAnimation": "Explode"}))


def test_footer_badge_can_go():
    assert 'made with <b>misa.lol</b>' in render_public_profile(_cfg())
    html = render_public_profile(_cfg({"hideBrand": True}))
    assert "made with" not in html
    assert 'data-report-open' in html  # the report button stays


def test_builtin_cursors_and_the_uploaded_one_wins():
    for name, url in BUILTIN_CURSORS.items():
        html = render_public_profile(_cfg({"cursor": name}))
        assert f'cursor:url("{url}") 12 12,auto;' in html
        assert url.startswith("data:image/svg+xml,") and "<" not in url and '"' not in url
    assert "cursor:url" not in render_public_profile(_cfg({"cursor": "default"}))
    assert "cursor:url" not in render_public_profile(_cfg({"cursor": "laser"}))
    html = render_public_profile(_cfg({"cursor": "star"}, {"cursor": {"url": "/uploads/u1/c.png"}}))
    assert "cursor:url('/uploads/u1/c.png') 4 4,auto;" in html and "data:image/svg+xml" not in html


def test_the_new_settings_are_gated_by_plan():
    cfg = {"settings": {"bioTypewriter": True, "entryAnimation": "Glitch", "hideBrand": True, "cursor": "star"}}
    assert set(gate_profile(cfg, "free")) == {"settings.bioTypewriter", "settings.entryAnimation", "settings.hideBrand", "settings.cursor"}
    assert cfg["settings"] == {"bioTypewriter": False, "entryAnimation": "None", "hideBrand": False, "cursor": "default"}
    cfg = {"settings": {"bioTypewriter": True, "entryAnimation": "Glitch", "hideBrand": True, "cursor": "star"}}
    assert gate_profile(cfg, "lifetime") == ["settings.cursor"]
    assert cfg["settings"]["bioTypewriter"] is True and cfg["settings"]["cursor"] == "default"
    cfg = {"settings": {"bioTypewriter": True, "entryAnimation": "Glitch", "hideBrand": True, "cursor": "snow"}}
    assert gate_profile(cfg, "supporter") == []


# ── v3.113: the Supporter set ──
def test_supporter_tag_sparkle_trail_and_gold_border_render():
    html = render_public_profile(_cfg({"supporterTag": True, "sparkleTrail": True, "goldBorder": True}))
    # v3.139: a screen reader read "rensupporter" — the tag is now announced as ", supporter" and the pill is decoration
    assert '<h1 class="name">ren<span class="sr-only">, supporter</span><span class="tag" title="Supporter" aria-hidden="true">supporter</span></h1>' in html
    assert '<canvas class="sparks" data-sparks aria-hidden="true"></canvas>' in html and "pointermove" in html
    assert 'class="card card--gold"' in html and "var(--ga,135deg)" in html and "@keyframes goldspin" in html
    plain = render_public_profile(_cfg())
    assert 'class="tag"' not in plain and '<canvas class="sparks"' not in plain and 'class="card card--gold"' not in plain
    # the gold border replaces the accent gradient border, and survives the plain-border setting too
    html = render_public_profile(_cfg({"goldBorder": True, "profileGradient": False}))
    assert "card--gold" in html and "#E6C36B" in html


def test_supporter_set_is_supporter_only():
    cfg = {"settings": {"supporterTag": True, "sparkleTrail": True, "goldBorder": True}}
    assert set(gate_profile(cfg, "lifetime")) == {"settings.supporterTag", "settings.sparkleTrail", "settings.goldBorder"}
    assert cfg["settings"] == {"supporterTag": False, "sparkleTrail": False, "goldBorder": False}
    cfg = {"settings": {"supporterTag": True, "sparkleTrail": True, "goldBorder": True}}
    assert gate_profile(cfg, "supporter") == []


# ── v3.114: page fonts and player styles ──
def test_page_fonts_load_only_when_chosen_and_scale_the_type():
    from app.profile_page import PAGE_FONTS
    plain = render_public_profile(_cfg())
    assert "family=VT323" not in plain and "--font:'Inter'" in plain and "--fs:1.0" in plain
    html = render_public_profile(_cfg({"font": "vt323"}))
    assert "&family=VT323&display=swap" in html and "--font:'VT323'" in html and "--fs:1.24" in html
    assert "font-size:calc(30px * var(--fs))" in html
    # playfair reuses the base request with the heavier weights; unknown keys fall back to Inter
    assert "Playfair+Display:ital,wght@0,400;0,700;0,800;1,400" in render_public_profile(_cfg({"font": "playfair"}))
    assert "--font:'Inter'" in render_public_profile(_cfg({"font": "comic"}))
    assert set(PAGE_FONTS) == {"inter", "playfair", "cormorant", "space-mono", "caveat", "vt323", "bebas", "unifraktur"}


def test_player_styles():
    assets = {"audio": {"url": "https://example.com/a.mp3", "name": "graveyard shift"}, "audioEnabled": True}
    for style in ("bars", "minimal", "vinyl"):
        html = render_public_profile(_cfg({"playerStyle": style}, assets))
        assert f'class="player player--{style}"' in html
    assert 'class="player player--bars"' in render_public_profile(_cfg({"playerStyle": "cassette"}, assets))
    assert "@keyframes spin" in render_public_profile(_cfg({"playerStyle": "vinyl"}, assets))


def test_fonts_and_player_are_gated_and_two_fonts_are_supporter_only():
    cfg = {"settings": {"font": "vt323", "playerStyle": "vinyl"}}
    assert set(gate_profile(cfg, "free")) == {"settings.font", "settings.playerStyle"}
    assert cfg["settings"] == {"font": "inter", "playerStyle": "bars"}
    cfg = {"settings": {"font": "vt323", "playerStyle": "vinyl"}}
    assert gate_profile(cfg, "lifetime") == [] and cfg["settings"]["font"] == "vt323"
    for exclusive in ("unifraktur", "cormorant"):
        cfg = {"settings": {"font": exclusive}}
        assert gate_profile(cfg, "lifetime") == ["settings.font"] and cfg["settings"]["font"] == "inter"
        cfg = {"settings": {"font": exclusive}}
        assert gate_profile(cfg, "supporter") == [] and cfg["settings"]["font"] == exclusive


# ── v3.115: content blocks and the custom share card ──
def test_content_blocks_render_in_place_and_escape():
    blocks = [
        {"type": "status", "text": "recording the EP", "place": "top"},
        {"type": "heading", "text": "shows"},
        {"type": "text", "text": "oct 3 — berlin\nnov 1 — leipzig"},
        {"type": "quote", "text": "less, <b>but</b> louder."},
        {"type": "divider"},
        {"type": "script", "text": "alert(1)"},
        {"type": "text", "text": "hidden", "enabled": False},
        {"type": "heading", "text": "   "},
    ]
    html = render_public_profile(_cfg({"blocks": blocks}, socials=[{"id": "s1", "platform": "Spotify", "label": "new single", "value": "open.spotify.com/x", "enabled": True}]))
    assert html.index('class="blk blk--now"') < html.index('<div class="links links--pill">') < html.index('class="blk blk--h"')
    assert '<span class="blk__k">currently</span> recording the EP</p>' in html
    assert '<p class="blk blk--p">oct 3 — berlin\nnov 1 — leipzig</p>' in html
    assert '<blockquote class="blk blk--q">less, &lt;b&gt;but&lt;/b&gt; louder.</blockquote>' in html and "<b>but</b>" not in html
    assert '<hr class="blk blk--hr" aria-hidden="true">' in html
    assert "alert(1)" not in html and ">hidden<" not in html and html.count('class="blk blk--h"') == 1
    assert '<div class="blocks">' not in render_public_profile(_cfg({"blocks": []}))
    assert '<div class="blocks">' not in render_public_profile(_cfg({"blocks": "nope"}))


def test_blocks_and_share_card_are_lifetime():
    cfg = {"settings": {"blocks": [{"type": "heading", "text": "x"}], "shareCard": {"tagline": "hi", "style": "mono"}}}
    assert set(gate_profile(cfg, "free")) == {"settings.blocks", "settings.shareCard"}
    assert cfg["settings"] == {"blocks": [], "shareCard": None}
    cfg = {"settings": {"blocks": [], "shareCard": {"tagline": "hi"}}}
    assert gate_profile(cfg, "free") == ["settings.shareCard"]  # an empty list is nothing to clear
    cfg = {"settings": {"blocks": [{"type": "heading", "text": "x"}], "shareCard": {"tagline": "hi"}}}
    assert gate_profile(cfg, "lifetime") == []


def test_custom_share_card_styles_and_tagline():
    from app.share_card import render_profile_card
    base = {"profile": {"username": "ren", "displayName": "ren", "description": "graveyard shift."}, "settings": {"accentColor": "#F00646"}, "badges": []}
    plain = render_profile_card(base)
    assert plain[:8] == b"\x89PNG\r\n\x1a\n"
    for style in ("glow", "poster", "mono"):
        cfg = dict(base, settings={"accentColor": "#F00646", "shareCard": {"style": style, "tagline": "the night shift never ends."}})
        png = render_profile_card(cfg)
        assert png[:8] == b"\x89PNG\r\n\x1a\n" and png != plain
    # a poster on a light accent keeps dark text; an unknown style is the glow; a long tagline is trimmed, not rejected
    render_profile_card(dict(base, settings={"accentColor": "#EEE8E2", "shareCard": {"style": "poster"}}))
    assert render_profile_card(dict(base, settings={"accentColor": "#F00646", "shareCard": {"style": "neon"}})) == plain
    render_profile_card(dict(base, settings={"accentColor": "#F00646", "shareCard": {"tagline": "x" * 500, "showBio": False}}))


# ── v3.116: link styles, avatar frames, living backgrounds, the tab title ──
def test_link_styles_avatar_frames_backgrounds_and_tab_title_render():
    socials = [{"id": "s1", "platform": "Spotify", "label": "new single", "value": "open.spotify.com/x", "enabled": True}]
    for style in ("pill", "outline", "ghost", "brutal", "glass"):
        assert f'<div class="links links--{style}">' in render_public_profile(_cfg({"linkStyle": style}, socials=socials))
    assert '<div class="links links--pill">' in render_public_profile(_cfg({"linkStyle": "neon"}, socials=socials))
    for frame in ("ring", "halo", "pixel", "petals"):
        html = render_public_profile(_cfg({"avatarFrame": frame}))
        assert f'<div class="avatar-wrap frame--{frame}"><div class="avatar avatar--letter"' in html
    assert 'class="avatar-wrap' not in render_public_profile(_cfg({"avatarFrame": "none"}))
    for fx in ("rain", "snow", "embers", "petals"):
        html = render_public_profile(_cfg({"backgroundEffect": fx.title()}))
        assert f'class="bg-fx fx-{fx}"' in html and f"@keyframes {fx}" in html
    for mode in ("breathe", "scroll", "blink"):
        assert f"var tabMode='{mode}'" in render_public_profile(_cfg({"tabTitle": mode}))
    assert "var tabMode=''" in render_public_profile(_cfg({"tabTitle": "spin"}))


def test_frames_and_tab_title_are_lifetime_link_styles_free():
    cfg = {"settings": {"linkStyle": "brutal", "avatarFrame": "ring", "tabTitle": "blink", "backgroundEffect": "Rain"}}
    assert set(gate_profile(cfg, "free")) == {"settings.avatarFrame", "settings.tabTitle", "settings.backgroundEffect"}
    assert cfg["settings"]["linkStyle"] == "brutal" and cfg["settings"]["avatarFrame"] == "none" and cfg["settings"]["tabTitle"] == "none"
    cfg = {"settings": {"avatarFrame": "ring", "tabTitle": "blink", "backgroundEffect": "Rain"}}
    assert gate_profile(cfg, "lifetime") == []


# ── v3.117: the guestbook ──
def test_guestbook_renders_signatures_and_the_form():
    sigs = [{"id": "a", "name": "peach", "line": "saw you at urban spree.", "at": 1}, {"id": "b", "name": "<b>x</b>", "line": "hi", "at": 2}, {"id": "c", "name": "", "line": "nameless", "at": 3}]
    html = render_public_profile(_cfg({"guestbook": True}), signatures=sigs)
    assert html.count('<li class="slip"') == 2 and "&lt;b&gt;x&lt;/b&gt;" in html and ">nameless<" not in html
    assert 'data-book-form' in html and "/api/v1/guestbook/ren" in html and "Caveat:wght@600" in html
    assert "nobody has signed yet" in render_public_profile(_cfg({"guestbook": True}), signatures=[])
    assert 'class="book"' not in render_public_profile(_cfg(), signatures=sigs)


def test_guestbook_api_sign_moderate_show(client, world):
    world.profiles[world.user.id]["settings"]["guestbook"] = True
    # a visitor signs (twice: the second is the same visitor the same day)
    r = client.post("/api/v1/guestbook/ren", json={"name": "  peach ", "line": "saw   you at urban spree."}, headers={"user-agent": "Mozilla/5.0 a"})
    assert r.status_code == 201 and "pile" in r.json()["message"]
    assert client.post("/api/v1/guestbook/ren", json={"name": "peach", "line": "again"}, headers={"user-agent": "Mozilla/5.0 a"}).status_code == 429
    # another visitor, a page without a book, a name that isn't a page, empty words
    assert client.post("/api/v1/guestbook/ren", json={"name": "lune", "line": "night bus."}, headers={"user-agent": "Mozilla/5.0 b", "x-forwarded-for": "10.0.0.2"}).status_code == 201
    world.profiles[world.user.id]["settings"]["guestbook"] = False
    assert client.post("/api/v1/guestbook/ren", json={"name": "x", "line": "y"}, headers={"user-agent": "Mozilla/5.0 c", "x-forwarded-for": "10.0.0.3"}).status_code == 404
    world.profiles[world.user.id]["settings"]["guestbook"] = True
    assert client.post("/api/v1/guestbook/nobody_here", json={"name": "x", "line": "y"}, headers={"x-forwarded-for": "10.0.0.4"}).status_code == 404
    assert client.post("/api/v1/guestbook/ren", json={"name": "   ", "line": "y"}, headers={"x-forwarded-for": "10.0.0.5"}).status_code == 400
    # nothing shows until the owner approves
    assert client.get("/api/v1/guestbook/ren").json() == {"entries": []}
    mine = client.get("/api/v1/me/guestbook").json()
    assert [e["name"] for e in mine["pending"]] == ["lune", "peach"] and mine["pending"][1]["line"] == "saw you at urban spree." and mine["approved"] == []
    pid = mine["pending"][1]["id"]
    assert client.post(f"/api/v1/me/guestbook/{pid}/approve").status_code == 200
    assert client.post(f"/api/v1/me/guestbook/{pid}/approve").status_code == 404
    shown = client.get("/api/v1/guestbook/ren").json()["entries"]
    assert [e["name"] for e in shown] == ["peach"] and "id" in shown[0] and "ip" not in shown[0]
    page = client.get("/ren", headers={"user-agent": "Mozilla/5.0 person"}).text
    assert '<li class="slip"' in page and "saw you at urban spree." in page and "night bus" not in page
    # bin the other, bin the shown one
    other = client.get("/api/v1/me/guestbook").json()["pending"][0]["id"]
    assert client.delete(f"/api/v1/me/guestbook/{other}").status_code == 200
    assert client.delete(f"/api/v1/me/guestbook/{pid}").status_code == 200
    assert client.get("/api/v1/me/guestbook").json() == {"pending": [], "approved": []}
    # signed out: the owner endpoints are closed
    world.user = None
    assert client.get("/api/v1/me/guestbook").status_code == 401


# ── v3.118: live presence, retro hit counters, the clock block ──
def test_presence_line_counts_or_hides():
    html = render_public_profile(_cfg({"presence": True}), here=3)
    assert '<p class="here" data-here>' in html and "3 people here right now" in html and "/api/v1/presence/ren" in html
    assert "just you here right now" in render_public_profile(_cfg({"presence": True}), here=1)
    assert '<p class="here" data-here hidden>' in render_public_profile(_cfg({"presence": True}), here=None)
    assert '<p class="here"' not in render_public_profile(_cfg(), here=3)


def test_hit_counter_styles_replace_the_plain_views():
    html = render_public_profile(_cfg({"counterStyle": "odometer"}), views=12412)
    assert 'class="odo odo--odometer" data-odo role="img" aria-label="12,412 views"' in html and "you are visitor no." in html
    assert html.count('<span class="odo__d">') == 6 and 'style="--n:0;--i:0"' in html and 'style="--n:2;--i:5"' in html
    assert '<span class="views">' not in html
    assert html.count('<span class="odo__d">') == 6  # padded to six digits
    assert render_public_profile(_cfg({"counterStyle": "lcd"}), views=1234567).count('<span class="odo__d">') == 7
    assert "odo--flip" in render_public_profile(_cfg({"counterStyle": "flip"}), views=1)
    plain = render_public_profile(_cfg({"counterStyle": "odometer", "showViews": False}), views=5)
    assert '<div class="odo' not in plain and '<span class="views">' not in plain
    assert '<span class="views">' in render_public_profile(_cfg({"counterStyle": "nonsense"}), views=5)


def test_clock_block_shows_the_owners_hour():
    blocks = [
        {"type": "clock", "tz": "Europe/Berlin", "place": "top"},
        {"type": "clock", "tz": "America/Los_Angeles", "text": "LA"},
        {"type": "clock", "tz": "Nope/City"},
        {"type": "clock", "tz": "../../etc/passwd"},
        {"type": "clock", "tz": ""},
    ]
    html = render_public_profile(_cfg({"blocks": blocks}))
    assert html.count('class="blk blk--clock"') == 2
    assert 'data-clock="Europe/Berlin"' in html and "in berlin</span>" in html and 'data-clock="America/Los_Angeles"' in html and "in LA</span>" in html
    assert "Nope" not in html and "passwd" not in html
    import re
    assert re.search(r'<time class="blk__time" datetime="\d{4}-\d\d-\d\dT\d\d:\d\d[+-]\d{4}" data-clock="Europe/Berlin">1?\d<span class="blk__colon">:</span>\d\d [ap]m</time>', html)


def test_counter_style_is_lifetime_presence_free():
    cfg = {"settings": {"counterStyle": "odometer", "presence": True}}
    assert gate_profile(cfg, "free") == ["settings.counterStyle"] and cfg["settings"] == {"counterStyle": "plain", "presence": True}
    assert gate_profile({"settings": {"counterStyle": "lcd"}}, "lifetime") == []


def test_presence_api_counts_visitors_for_a_while(client, world):
    world.profiles[world.user.id]["settings"]["presence"] = True
    a = {"user-agent": "Mozilla/5.0 a", "x-forwarded-for": "10.0.0.1"}
    b = {"user-agent": "Mozilla/5.0 b", "x-forwarded-for": "10.0.0.2"}
    # the page itself counts its visitor on render
    page = client.get("/ren", headers=a).text
    assert "just you here right now" in page
    assert client.post("/api/v1/presence/ren", headers=a).json() == {"here": 1}
    assert client.post("/api/v1/presence/ren", headers=b).json() == {"here": 2}
    assert client.post("/api/v1/presence/ren", headers=a).json() == {"here": 2}  # a heartbeat, not a new person
    assert "2 people here right now" in client.get("/ren", headers=b).text
    # a crawler is answered but never counted
    assert client.post("/api/v1/presence/ren", headers={"user-agent": "Discordbot/2.0", "x-forwarded-for": "10.0.0.9"}).json() == {"here": 2}
    # leaving drops you at once
    assert client.post("/api/v1/presence/ren/leave", headers=b).status_code == 204
    assert client.post("/api/v1/presence/ren", headers=a).json() == {"here": 1}
    # a page with presence off, and a name that isn't a page
    world.profiles[world.user.id]["settings"]["presence"] = False
    assert client.post("/api/v1/presence/ren", headers=a).status_code == 404
    assert '<p class="here"' not in client.get("/ren", headers=a).text
    assert client.post("/api/v1/presence/nobody_here", headers=a).status_code == 404
    assert client.post("/api/v1/presence/nobody_here/leave", headers=a).status_code == 204


# ── v3.119: page moods, the secret word ──
def test_mood_layer_only_when_on():
    assert '<div class="mood" data-mood aria-hidden="true"></div>' in render_public_profile(_cfg({"mood": True}))
    assert '<div class="mood"' not in render_public_profile(_cfg())


def test_secret_word_keeps_the_word_and_the_link_out_of_the_source():
    from app.profile_page import _secret
    import hashlib
    html = render_public_profile(_cfg({"secret": {"word": " Night Bus! ", "url": "https://example.com/b-side", "label": "<i>the b-side</i>"}}))
    assert 'class="secret" data-secret' in html and 'data-n="8"' in html and "&lt;i&gt;the b-side&lt;/i&gt;" in html and 'data-secret-ask' in html
    assert "nightbus" not in html and "example.com/b-side" not in html
    assert 'data-v="' + hashlib.sha256(b"misa-secret|nightbus").hexdigest() + '"' in html
    # the keystream round-trips
    v, c, lab, n = _secret({"word": "nightbus", "url": "https://example.com/b-side"})
    key = hashlib.sha256(b"nightbus").digest()
    stream = b"".join(hashlib.sha256(key + bytes([i])).digest() for i in range(4))
    assert bytes(a ^ b for a, b in zip(bytes.fromhex(c), stream)).decode() == "https://example.com/b-side" and lab == "you found it" and n == 8
    # too short, no link, not a dict: no secret at all
    for bad in ({"word": "ab", "url": "https://x.y"}, {"word": "abc"}, {"word": "abc", "url": "javascript:alert(1)"}, "abc", None):
        assert 'class="secret"' not in render_public_profile(_cfg({"secret": bad}))


def test_mood_and_secret_are_lifetime():
    cfg = {"settings": {"mood": True, "secret": {"word": "abc", "url": "https://x.y"}}}
    assert set(gate_profile(cfg, "free")) == {"settings.mood", "settings.secret"} and cfg["settings"] == {"mood": False, "secret": None}
    assert gate_profile({"settings": {"mood": True, "secret": {"word": "abc", "url": "https://x.y"}}}, "lifetime") == []


# ── v3.122: now playing ──
def test_now_playing_block_typed_and_live():
    blocks = [{"type": "nowplaying", "text": "graveyard shift — ren", "url": "https://example.com/t"}, {"type": "nowplaying", "lb": "ren_lb"}, {"type": "nowplaying", "lb": "bad name!"}, {"type": "nowplaying"}]
    html = render_public_profile(_cfg({"blocks": blocks}))
    assert html.count('class="blk blk--np') == 2  # the typed one and the live one; the bad name and the empty one are skipped
    assert '<a class="np__t" data-np-t href="https://example.com/t"' in html and "graveyard shift — ren" in html
    assert '<p class="blk blk--np" data-np="ren_lb" hidden>' in html  # nothing known yet: hidden until the poll answers
    assert "setTimeout(npTick,400)" in html and "/api/v1/nowplaying/ren" in html
    live = {"ren_lb": {"ok": True, "playing": True, "track": "Night <Bus>", "artist": "lune", "at": 1}}
    html = render_public_profile(_cfg({"blocks": blocks[1:2]}), live=live)
    assert '<p class="blk blk--np is-live" data-np="ren_lb">' in html and "Night &lt;Bus&gt; — lune" in html and ">now playing<" in html and "setTimeout(npTick,45000)" in html
    import time
    live = {"ren_lb": {"ok": True, "playing": False, "track": "Old One", "artist": "x", "at": int(time.time()) - 600}}
    html = render_public_profile(_cfg({"blocks": blocks[1:2]}), live=live)
    assert ">last played · 10 min ago<" in html and "is-live" not in html.split('<p class="blk blk--np')[1][:40]


def test_now_playing_lookup_and_cache(client, world, monkeypatch):
    import asyncio
    from app.core import nowplaying
    calls = []

    async def fake_fetch(url):
        calls.append(url)
        if url.endswith("/playing-now"):
            return {"payload": {"listens": [{"track_metadata": {"track_name": "Night Bus", "artist_name": "lune"}}]}} if "ren_lb" in url else {"payload": {"listens": []}}
        if "count=1" in url:
            return {"payload": {"listens": [{"listened_at": 1757400000, "track_metadata": {"track_name": "Old One", "artist_name": "x"}}]}} if "quiet" in url else None
        return None
    monkeypatch.setattr(nowplaying, "fetch_json", fake_fetch)
    world.profiles[world.user.id]["settings"]["blocks"] = [{"type": "nowplaying", "lb": "ren_lb", "enabled": True}]
    r = client.get("/api/v1/nowplaying/ren")
    assert r.status_code == 200 and r.json() == {"playing": True, "track": "Night Bus", "artist": "lune", "ago": ""}
    assert client.get("/api/v1/nowplaying/ren").json()["track"] == "Night Bus" and len(calls) == 1  # the second answer came from the cache
    # a page render uses the cache too, and never the network
    page = client.get("/ren", headers={"user-agent": "Mozilla/5.0 x"}).text
    assert "Night Bus — lune" in page and 'class="blk blk--np is-live"' in page and len(calls) == 1
    # someone who scrobbled but isn't playing now: last played, with an age
    world.profiles[world.user.id]["settings"]["blocks"] = [{"type": "nowplaying", "lb": "quiet_one"}]
    d = client.get("/api/v1/nowplaying/ren").json()
    assert d["playing"] is False and d["track"] == "Old One" and d["ago"].endswith(" ago")
    # no block, unknown name, a dead ListenBrainz name
    world.profiles[world.user.id]["settings"]["blocks"] = []
    assert client.get("/api/v1/nowplaying/ren").status_code == 404
    assert client.get("/api/v1/nowplaying/nobody_here").status_code == 404
    world.profiles[world.user.id]["settings"]["blocks"] = [{"type": "nowplaying", "lb": "dead"}]
    assert client.get("/api/v1/nowplaying/ren").json() == {"playing": False, "track": "", "artist": "", "ago": ""}
    assert nowplaying.ago(0) == "" and nowplaying.ago(100, 150) == "just now" and nowplaying.ago(0 + 1, 3601) == "1 h ago" and nowplaying.ago(1, 90000) == "1 d ago"


# ── v3.123: visitor doodles (the chalkboard) ──
def test_chalkboard_renders_drawings_and_the_form():
    from app.core.doodles import clean, svg
    drawings = [{"id": "a", "s": [[10, 10, 50, 60], [3, 3]], "c": "pink", "at": 1}, {"id": "b", "s": "nope", "c": "chalk", "at": 2}]
    html = render_public_profile(_cfg({"doodles": True}), drawings=drawings)
    assert html.count('<li class="tile"') == 1 and '<path d="M10 10L50 60"/>' in html and 'style="color:#ff9ac4"' in html
    assert 'data-board-form' in html and 'data-board-canvas' in html and "/api/v1/doodles/ren" in html and "Caveat:wght@600" in html
    assert html.count('name="colour"') == 5
    assert "nobody has drawn yet" in render_public_profile(_cfg({"doodles": True}), drawings=[])
    assert '<section class="board"' not in render_public_profile(_cfg(), drawings=drawings)
    # clean(): clamps, rounds, drops repeats and junk, caps
    assert clean([[10.4, 10.6, 50, 60, 50.2, 60.3, 999, -5], [1], "x", [[3, 3], [4, 4]]], "SKY") == ([[10, 11, 50, 60, 200, 0], [3, 3, 4, 4]], "sky")
    assert clean([], "chalk") is None and clean("x", "chalk") is None and clean([[1]], "chalk") is None
    big = [[i % 200, (i * 7) % 140] for i in range(1000)]
    strokes, _ = clean([big] * 50, "nope")
    assert len(strokes) <= 40 and all(len(st) <= 800 for st in strokes) and sum(len(st) // 2 for st in strokes) <= 3400
    assert 'stroke="currentColor"' in svg({"s": [[1, 2, 3, 4]], "c": "accent"}) and "var(--accent)" in svg({"s": [[1, 2, 3, 4]], "c": "accent"})


def test_chalkboard_api_draw_moderate_show(client, world):
    world.profiles[world.user.id]["settings"]["doodles"] = True
    a = {"user-agent": "Mozilla/5.0 a", "x-forwarded-for": "10.0.0.1"}
    b = {"user-agent": "Mozilla/5.0 b", "x-forwarded-for": "10.0.0.2"}
    r = client.post("/api/v1/doodles/ren", json={"strokes": [[10, 10, 50, 60, 90, 20]], "colour": "pink"}, headers=a)
    assert r.status_code == 201 and "Chalked" in r.json()["message"]
    assert client.post("/api/v1/doodles/ren", json={"strokes": [[1, 1, 2, 2]], "colour": "chalk"}, headers=a).status_code == 429  # one a day
    assert client.post("/api/v1/doodles/ren", json={"strokes": [[5, 5, 5, 5]], "colour": "chalk"}, headers=b).status_code == 201  # a dot is a drawing
    assert client.post("/api/v1/doodles/ren", json={"strokes": [], "colour": "chalk"}, headers={"x-forwarded-for": "10.0.0.3"}).status_code == 400
    assert client.post("/api/v1/doodles/ren", json={"strokes": "x", "colour": "chalk"}, headers={"x-forwarded-for": "10.0.0.4"}).status_code == 422
    world.profiles[world.user.id]["settings"]["doodles"] = False
    assert client.post("/api/v1/doodles/ren", json={"strokes": [[1, 1, 2, 2]]}, headers={"x-forwarded-for": "10.0.0.5"}).status_code == 404
    world.profiles[world.user.id]["settings"]["doodles"] = True
    assert client.post("/api/v1/doodles/nobody_here", json={"strokes": [[1, 1, 2, 2]]}, headers={"x-forwarded-for": "10.0.0.6"}).status_code == 404
    # nothing shows until the owner approves
    assert client.get("/api/v1/doodles/ren").json() == {"entries": []}
    mine = client.get("/api/v1/me/doodles").json()
    assert len(mine["pending"]) == 2 and mine["approved"] == [] and mine["pending"][1]["c"] == "pink" and "<svg" in mine["pending"][1]["svg"] and "s" not in mine["pending"][1]
    pid = mine["pending"][1]["id"]
    assert client.post(f"/api/v1/me/doodles/{pid}/approve").status_code == 200
    assert client.post(f"/api/v1/me/doodles/{pid}/approve").status_code == 404
    shown = client.get("/api/v1/doodles/ren").json()["entries"]
    assert [e["id"] for e in shown] == [pid] and "M10 10L50 60L90 20" in shown[0]["svg"]
    page = client.get("/ren", headers={"user-agent": "Mozilla/5.0 person"}).text
    assert page.count('<li class="tile"') == 1 and "M10 10L50 60L90 20" in page
    other = client.get("/api/v1/me/doodles").json()["pending"][0]["id"]
    assert client.delete(f"/api/v1/me/doodles/{other}").status_code == 200 and client.delete(f"/api/v1/me/doodles/{pid}").status_code == 200
    assert client.get("/api/v1/me/doodles").json() == {"pending": [], "approved": []}
    world.user = None
    assert client.get("/api/v1/me/doodles").status_code == 401


# ── v3.124: a page that ages, milestone cards ──
def test_the_page_ages_with_the_account():
    from datetime import datetime, timedelta, timezone
    from app.profile_page import _age
    now = datetime(2026, 9, 9, 12, tzinfo=timezone.utc)
    assert _age("2026-09-09T10:00:00Z", now) == (0, "today") and _age("2026-09-01T10:00:00+00:00", now) == (8, "1 sep")
    assert _age("2026-07-01", now) == (70, "jul 2026") and _age("2024-03-05T00:00:00Z", now) == (918, "mar 2024")
    assert _age("garbage", now) is None and _age(None, now) is None and _age("", now) is None
    day = lambda d: (datetime.now(timezone.utc) - timedelta(days=d)).strftime("%Y-%m-%dT%H:%M:%SZ")
    fresh = render_public_profile(_cfg({"since": True}), since=day(2))
    assert '<main class="card age-new"' in fresh and '<span class="fresh">new here</span>' in fresh and '<span class="since">here since ' in fresh and '<span class="seal"' not in fresh
    month = render_public_profile(_cfg({"since": True}), since=day(45))
    assert '<main class="card age-month"' in month and '<span class="seal" aria-hidden="true" title="here since ' in month and "new here" not in month and '<i class="patina"' not in month
    year = render_public_profile(_cfg({"since": True}), since=day(800))
    assert '<main class="card age-year"' in year and 'class="seal seal--gold"' in year and "<b>2y</b>" in year and '<i class="patina" aria-hidden="true"></i>' in year
    off = render_public_profile(_cfg(), since=day(800))
    assert '<span class="since">' not in off and '<span class="seal' not in off and '<main class="card"' in off
    assert '<span class="since">' not in render_public_profile(_cfg({"since": True}), since=None)


def test_milestone_card_only_for_counts_really_crossed(client, world, monkeypatch):
    from app.milestone_card import reached, short, render_milestone
    import app.main as main_module
    assert reached(99) is None and reached(100) == 100 and reached(12412) == 10000 and reached(2_000_000) == 1_000_000
    assert (short(100), short(1000), short(100000), short(1000000)) == ("100", "1k", "100k", "1M")
    png = render_milestone({"profile": {"username": "ren", "displayName": "ren"}, "settings": {"accentColor": "#F00646"}}, 1000)
    assert png[:8] == b"\x89PNG\r\n\x1a\n" and len(png) > 20000
    # the route: views decide
    async def fake_views(uid):
        return 1500
    monkeypatch.setattr("app.core.analytics.total_views", fake_views)
    r = client.get("/ren/milestone.png?n=1000")
    assert r.status_code == 200 and r.headers["content-type"] == "image/png" and r.content[:4] == b"\x89PNG"
    assert client.get("/ren/milestone.png?n=10000").status_code == 404  # not there yet
    assert client.get("/ren/milestone.png?n=1234").status_code == 404  # not a milestone
    assert client.get("/ren/milestone.png").status_code == 404
    assert client.get("/nobody_here/milestone.png?n=100").status_code == 404
    # the page route passes the account's age through
    world.profiles[world.user.id]["settings"]["since"] = True
    page = client.get("/ren", headers={"user-agent": "Mozilla/5.0 x"}).text
    assert '<span class="since">here since ' in page and 'class="card age-month"' in page


# ── v3.125: weather where you are, the dead-links sweep ──
def test_weather_block_words_and_render():
    from app.core.weather import describe, temp, line, clean_place
    assert describe(0, True) == ("clear", "sun") and describe(0, False) == ("clear night", "moon") and describe(2, False) == ("cloudy night", "moon")
    assert describe(63, True) == ("raining", "rain") and describe(75, True) == ("heavy snow", "snow") and describe(95, False) == ("storms", "storm") and describe(999, True) == ("weather", "cloud")
    assert temp(11.4, "c") == "11°" and temp(-2.5, "c") == "-2°" and temp(11.4, "f") == "53°"
    assert line({"label": "berlin", "code": 61, "c": 11.2, "day": True}, "c") == ("raining in berlin", "11°", "rain")
    assert line({"label": "berlin", "code": 0, "c": 3, "day": False}, "f", "home") == ("clear night in home", "37°", "moon")
    assert clean_place(" São Paulo ") == "São Paulo" and clean_place("<x>") == "" and clean_place("a") == ""
    blocks = [{"type": "weather", "city": "Berlin", "place": "top"}, {"type": "weather", "city": "Tokyo", "unit": "F", "text": "home"}, {"type": "weather", "city": ""}]
    html = render_public_profile(_cfg({"blocks": blocks}), weather={"Berlin": {"label": "berlin", "code": 61, "c": 11.2, "day": True}})
    assert html.count('<p class="blk blk--wx"') == 2 and '<use href="#i-rain"/>' in html and ">raining in berlin<" in html and ">11°<" in html
    assert '<p class="blk blk--wx" data-wx hidden>' in html and "setTimeout(wxTick,500)" in html and "/api/v1/weather/ren" in html
    html = render_public_profile(_cfg({"blocks": blocks[:1]}), weather={"Berlin": {"label": "berlin", "code": 0, "c": 20, "day": True}})
    assert "setTimeout(wxTick,600000)" in html and '<use href="#i-sun"/>' in html


def test_weather_api_geocodes_once_and_caches(client, world, monkeypatch):
    from app.core import weather
    calls = []

    async def fake_fetch(url):
        calls.append(url)
        if "geocoding-api" in url:
            return {"results": [{"name": "Berlin", "latitude": 52.52, "longitude": 13.405}]} if "Berlin" in url else {"results": []}
        return {"current": {"temperature_2m": 11.2, "weather_code": 61, "is_day": 1}}
    monkeypatch.setattr(weather, "fetch_json", fake_fetch)
    world.profiles[world.user.id]["settings"]["blocks"] = [{"type": "weather", "city": "Berlin", "unit": "c"}]
    assert client.get("/api/v1/weather/ren").json() == {"line": "raining in berlin", "temp": "11°", "icon": "rain", "sky": "rain"}
    assert len(calls) == 2  # one geocode, one forecast
    assert client.get("/api/v1/weather/ren").json()["temp"] == "11°" and len(calls) == 2  # both cached
    page = client.get("/ren", headers={"user-agent": "Mozilla/5.0 x"}).text
    assert ">raining in berlin<" in page and len(calls) == 2  # the render used the cache
    world.profiles[world.user.id]["settings"]["blocks"] = [{"type": "weather", "city": "Nowhere Town"}]
    assert client.get("/api/v1/weather/ren").json() == {"line": "", "temp": "", "icon": "", "sky": ""}
    world.profiles[world.user.id]["settings"]["blocks"] = []
    assert client.get("/api/v1/weather/ren").status_code == 404 and client.get("/api/v1/weather/nobody_here").status_code == 404


def test_dead_links_sweep(client, world, monkeypatch):
    from app.api.v1 import linkcheck
    seen = []

    async def fake_check(client_, url):
        seen.append(url)
        if "dead" in url:
            return False, 404, "404 — this one's dead"
        if "slow" in url:
            return False, None, "timed out — slow or gone"
        return True, 200, "fine"
    monkeypatch.setattr(linkcheck, "check_url", fake_check)
    world.profiles[world.user.id]["socials"] = [
        {"id": "s1", "platform": "Spotify", "value": "open.spotify.com/x", "enabled": True, "displayMode": "link"},
        {"id": "s2", "platform": "Custom URL", "value": "https://example.com/dead", "enabled": True, "displayMode": "link"},
        {"id": "s3", "platform": "Custom URL", "value": "https://example.com/slow", "enabled": True, "displayMode": "link"},
        {"id": "s4", "platform": "Email", "value": "ren@example.com", "enabled": True, "displayMode": "link"},
        {"id": "s5", "platform": "Custom URL", "value": "https://example.com/off", "enabled": False, "displayMode": "link"},
        {"id": "s6", "platform": "Custom URL", "value": "http://localhost:8000/admin", "enabled": True, "displayMode": "link"},
        {"id": "s7", "platform": "Discord", "value": "ren#1234", "enabled": True, "displayMode": "text"},
    ]
    r = client.post("/api/v1/me/links/check")
    assert r.status_code == 200
    d = r.json()
    assert d["checked"] == 3 and [x["id"] for x in d["results"]] == ["s1", "s2", "s3"]
    assert d["results"][0] == {"id": "s1", "url": "https://open.spotify.com/x", "ok": True, "status": 200, "note": "fine"}
    assert d["results"][1]["ok"] is False and d["results"][1]["status"] == 404 and d["results"][2]["status"] is None
    assert "http://localhost:8000/admin" not in seen and not any("example.com/off" in u for u in seen)
    world.user = None
    assert client.post("/api/v1/me/links/check").status_code == 401


# ── v3.127: the visitor's-eye replay ────────────────────────────────────────────────────────────────────


def test_replay_groups_events_into_visits(world):
    import asyncio

    from app.core import replay

    async def run():
        uid = "u-replay"
        await replay.note(uid, "in", "aaaaaaaa", "tiktok.com", phone=True)
        await replay.note(uid, "tap", "aaaaaaaa", "s1")
        await replay.note(uid, "sign", "aaaaaaaa")
        await replay.note(uid, "in", "bbbbbbbb", "")                      # a second visitor, no referrer
        await replay.note(uid, "junk", "bbbbbbbb", "")                    # not a kind we keep
        await replay.note(uid, "in", "cccccccc", "not a host!")           # a referrer that isn't a host is dropped
        visits = await replay.visits(uid)
        return visits

    visits = asyncio.get_event_loop().run_until_complete(run())
    assert len(visits) == 3
    newest, middle, oldest = visits
    assert oldest["from"] == "tiktok.com" and oldest["device"] == "phone"
    assert [e["k"] for e in oldest["events"]] == ["in", "tap", "sign"] and oldest["taps"] == ["s1"]
    assert middle["from"] is None and middle["device"] == "desktop"
    assert newest["from"] is None                                          # “not a host!” was cleaned away


def test_replay_keeps_a_lid_on_it(world):
    import asyncio

    from app.core import replay

    async def run():
        uid = "u-lid"
        for i in range(replay.MAX + 40):
            await replay.note(uid, "in", f"{i:08d}", "")
        return await replay.events(uid), await replay.visits(uid)

    events, visits = asyncio.get_event_loop().run_until_complete(run())
    assert len(events) == replay.MAX and len(visits) == 10          # the list is capped, the answer is ten visits


def test_replay_api_says_when_it_is_off(client, world):
    world.profiles[world.user.id]["settings"]["replay"] = False
    r = client.get("/api/v1/me/replay")
    assert r.status_code == 200 and r.json()["on"] is False and r.json()["visits"] == []
    world.profiles[world.user.id]["settings"]["replay"] = True
    r = client.get("/api/v1/me/replay")
    assert r.status_code == 200 and r.json() == {"on": True, "visits": [], "kept_for_days": 7}
    world.user = None
    assert client.get("/api/v1/me/replay").status_code == 401


def test_replay_writes_only_when_it_is_on(client, world):
    world.profiles[world.user.id]["settings"]["replay"] = False
    assert client.get("/ren", headers={"user-agent": "Mozilla/5.0 (iPhone)"}).status_code == 200
    client.post("/api/v1/hit/ren/s1")
    assert client.get("/api/v1/me/replay").json()["visits"] == []

    world.profiles[world.user.id]["settings"]["replay"] = True
    assert client.get("/ren", headers={"user-agent": "Mozilla/5.0 (iPhone)", "referer": "https://www.tiktok.com/@ren"}).status_code == 200
    client.post("/api/v1/hit/ren/s1", headers={"user-agent": "Mozilla/5.0 (iPhone)"})
    visits = client.get("/api/v1/me/replay").json()["visits"]
    assert len(visits) == 1
    assert visits[0]["from"] == "www.tiktok.com" and visits[0]["device"] == "phone"
    assert [e["k"] for e in visits[0]["events"]] == ["in", "tap"] and visits[0]["taps"] == ["s1"]

    # a crawler is not a visit
    client.get("/ren", headers={"user-agent": "Discordbot/2.0"})
    assert len(client.get("/api/v1/me/replay").json()["visits"]) == 1


def test_replay_own_domain_is_not_a_referrer(client, world):
    world.profiles[world.user.id]["settings"]["replay"] = True
    assert client.get("/ren", headers={"referer": "https://misa.lol/explore", "user-agent": "Mozilla/5.0"}).status_code == 200
    visits = client.get("/api/v1/me/replay").json()["visits"]
    assert len(visits) == 1 and visits[0]["from"] is None and visits[0]["device"] == "desktop"


# ── v3.128: the ask box ─────────────────────────────────────────────────────────────────────────────────


def test_ask_box_answering_is_what_publishes(client, world):
    world.profiles[world.user.id]["settings"]["asks"] = True
    r = client.post("/api/v1/asks/ren", json={"question": "  what pedal   is that?  "})
    assert r.status_code == 201 and "answer" in r.json()["message"]
    mine = client.get("/api/v1/me/asks").json()
    assert len(mine["waiting"]) == 1 and mine["answered"] == []
    q = mine["waiting"][0]
    assert q["q"] == "what pedal is that?"                      # whitespace tidied, nothing about who asked
    assert set(q) == {"id", "q", "at"}
    assert client.get("/api/v1/asks/ren").json() == {"entries": []}   # unanswered is never public

    r = client.post(f"/api/v1/me/asks/{q['id']}/answer", json={"answer": "a rat clone, mostly"})
    assert r.status_code == 200 and r.json()["entry"]["a"] == "a rat clone, mostly"
    public = client.get("/api/v1/asks/ren").json()["entries"]
    assert len(public) == 1 and public[0]["q"] == "what pedal is that?" and public[0]["a"] == "a rat clone, mostly"

    # the page shows it, question above answer
    from app.profile_page import render_public_profile
    html = render_public_profile(_cfg({"asks": True}), asked=public)
    assert '<p class="qa__q">what pedal is that?</p>' in html and '<p class="qa__a">a rat clone, mostly</p>' in html
    assert 'data-ask-form' in html and "ask me anything" in html

    # answering again rewrites it, and it stays in place
    r = client.post(f"/api/v1/me/asks/{q['id']}/answer", json={"answer": "ok fine, two rat clones"})
    assert r.status_code == 200
    assert client.get("/api/v1/asks/ren").json()["entries"][0]["a"] == "ok fine, two rat clones"

    # binning takes it off the page
    assert client.delete(f"/api/v1/me/asks/{q['id']}").status_code == 200
    assert client.get("/api/v1/asks/ren").json()["entries"] == []


def test_ask_box_is_shut_unless_it_is_on(client, world):
    world.profiles[world.user.id]["settings"]["asks"] = False
    assert client.post("/api/v1/asks/ren", json={"question": "hello?"}).status_code == 404
    assert client.get("/api/v1/asks/ren").status_code == 404
    assert client.post("/api/v1/asks/nobody_here", json={"question": "hello?"}).status_code == 404
    from app.profile_page import render_public_profile
    assert '<form class="asks__form"' not in render_public_profile(_cfg({}))   # the page's own script mentions the hook; the markup is the test


def test_ask_box_one_question_a_day_and_no_empty_ones(client, world):
    world.profiles[world.user.id]["settings"]["asks"] = True
    assert client.post("/api/v1/asks/ren", json={"question": "   "}).status_code == 400      # blank once tidied
    assert client.post("/api/v1/asks/ren", json={"question": "first"}).status_code == 201
    assert client.post("/api/v1/asks/ren", json={"question": "second"}).status_code == 429   # same visitor, same day
    assert len(client.get("/api/v1/me/asks").json()["waiting"]) == 1


def test_ask_box_answers_need_words(client, world):
    world.profiles[world.user.id]["settings"]["asks"] = True
    client.post("/api/v1/asks/ren", json={"question": "are you ok"})
    qid = client.get("/api/v1/me/asks").json()["waiting"][0]["id"]
    assert client.post(f"/api/v1/me/asks/{qid}/answer", json={"answer": "   "}).status_code == 400
    assert client.post("/api/v1/me/asks/nope/answer", json={"answer": "hi"}).status_code == 404
    world.user = None
    assert client.get("/api/v1/me/asks").status_code == 401
    assert client.delete("/api/v1/me/asks/x").status_code == 401


# ── v3.129: the time capsule ────────────────────────────────────────────────────────────────────────────


def test_capsule_keeps_the_words_off_the_page_until_the_day():
    from app.profile_page import render_public_profile
    sealed = {"text": "i hope you kept the band together", "at": "2099-12-24"}
    html = render_public_profile(_cfg({"capsule": sealed}))
    assert 'class="capsule"' in html and 'data-capsule="2099-12-24T00:00:00Z"' in html
    assert "opens 24 dec 2099" in html
    assert "kept the band together" not in html          # the point: the words are not in the source

    opened = {"text": "i hope you kept the band together", "at": "2020-12-24"}
    html = render_public_profile(_cfg({"capsule": opened}))
    assert 'class="capsule is-open"' in html and "i hope you kept the band together" in html
    assert "opened 24 dec 2020" in html


def test_capsule_ignores_nonsense():
    from app.profile_page import render_public_profile
    for bad in ({"text": "", "at": "2099-12-24"}, {"text": "hi", "at": ""}, {"text": "hi", "at": "24/12/2099"},
                {"text": "hi", "at": "2099-13-45"}, "nope", None):
        assert 'class="capsule' not in render_public_profile(_cfg({"capsule": bad}))


def test_capsule_is_a_lifetime_perk(client, world):
    world.plan = None
    r = client.put("/api/v1/profile/me", json={"profile": {"username": "ren", "displayName": "ren"},
                                              "settings": {"capsule": {"text": "for later", "at": "2099-12-24"}},
                                              "socials": [], "badges": [], "assets": {}})
    assert r.status_code == 200
    assert r.json()["profile"]["settings"].get("capsule") in (None, {})
    assert "settings.capsule" in r.json().get("cleared", [])

    world.plan = "lifetime"
    r = client.put("/api/v1/profile/me", json={"profile": {"username": "ren", "displayName": "ren"},
                                              "settings": {"capsule": {"text": "for later", "at": "2099-12-24"}},
                                              "socials": [], "badges": [], "assets": {}})
    assert r.status_code == 200 and r.json()["profile"]["settings"]["capsule"]["at"] == "2099-12-24"


# ── v3.130: the sky — the owner's real weather, over the page ────────────────────────────────────────────


def test_sky_states_come_from_the_weather_code():
    from app.core.weather import effect
    assert effect(61, True) == "rain" and effect(95, True) == "storm"
    assert effect(73, True) == "snow" and effect(45, True) == "fog"
    assert effect(3, True) == "cloud" and effect(2, True) == "cloud"
    assert effect(0, True) == "clear" and effect(0, False) == "night"
    assert effect(1, False) == "night" and effect(2, False) == "cloud"


def test_sky_renders_only_when_a_city_is_set():
    from app.profile_page import render_public_profile
    assert 'class="sky' not in render_public_profile(_cfg({}))
    html = render_public_profile(_cfg({"sky": "berlin"}), sky="rain")
    assert 'class="sky sky--rain" data-sky="berlin"' in html and ".sky--rain i" in html
    # a state the server doesn't know is simply not worn — the page's poll fills it in
    assert 'class="sky" data-sky="berlin"' in render_public_profile(_cfg({"sky": "berlin"}), sky="tornado")
    assert 'class="sky" data-sky="berlin"' in render_public_profile(_cfg({"sky": "berlin"}))


def test_sky_reads_the_cache_on_a_render(client, world, monkeypatch):
    from app.core import weather
    calls = []

    async def fake_fetch(url):
        calls.append(url)
        if "geocoding-api" in url:
            return {"results": [{"name": "Berlin", "latitude": 52.52, "longitude": 13.405}]}
        return {"current": {"temperature_2m": -2.0, "weather_code": 73, "is_day": 0}}
    monkeypatch.setattr(weather, "fetch_json", fake_fetch)
    world.profiles[world.user.id]["settings"]["sky"] = "Berlin"
    world.profiles[world.user.id]["settings"]["blocks"] = [{"type": "weather", "city": "Berlin", "unit": "c"}]
    assert client.get("/api/v1/weather/ren").json()["sky"] == "snow"      # warms the cache
    page = client.get("/ren", headers={"user-agent": "Mozilla/5.0 x"}).text
    assert 'class="sky sky--snow"' in page and len(calls) == 2            # the render used the cache, not the network


def test_sky_is_a_lifetime_perk(client, world):
    world.plan = None
    body = {"profile": {"username": "ren", "displayName": "ren"}, "settings": {"sky": "berlin"}, "socials": [], "badges": [], "assets": {}}
    r = client.put("/api/v1/profile/me", json=body)
    assert r.status_code == 200 and not r.json()["profile"]["settings"].get("sky") and "settings.sky" in r.json().get("cleared", [])
    world.plan = "lifetime"
    r = client.put("/api/v1/profile/me", json=body)
    assert r.status_code == 200 and r.json()["profile"]["settings"]["sky"] == "berlin"


# ── v3.131: everything at once ──────────────────────────────────────────────────────────────────────────


def test_a_text_block_does_not_steal_the_page_colour():
    """v3.131: the blocks loop reused `text`, so a text/quote/heading block overwrote the page's text colour —
    `--text: tapes at the merch table` — and every rule built on var(--text) (the shimmer name above all) died."""
    from app.profile_page import render_public_profile
    html = render_public_profile(_cfg({
        "textColor": "#F2F2F0", "usernameEffect": "shimmer",
        "blocks": [{"id": "b1", "type": "text", "text": "tapes at the merch table, cash only.", "place": "bottom", "enabled": True}],
    }))
    assert "--text:#F2F2F0;" in html
    assert '<p class="blk blk--p">tapes at the merch table, cash only.</p>' in html


def test_everything_at_once_still_renders_every_part():
    from app.profile_page import render_public_profile
    cfg = _cfg({
        "guestbook": True, "doodles": True, "asks": True, "presence": True, "since": True, "mood": True,
        "counterStyle": "odometer", "sky": "berlin", "usernameEffect": "shimmer", "usernameGlow": True,
        "capsule": {"text": "for later", "at": "2099-12-24"},
        "secret": {"word": "nightbus", "url": "https://example.com/b", "label": "the b-side"},
        "blocks": [{"id": "b1", "type": "heading", "text": "what i'm up to", "place": "top", "enabled": True},
                   {"id": "b2", "type": "quote", "text": "a laundrette in leipzig.", "place": "bottom", "enabled": True}],
    })
    html = render_public_profile(cfg, views=12412, signatures=[{"id": "g1", "name": "peach", "line": "hi", "at": 1}],
                                 here=3, drawings=[], since="2026-07-01T10:00:00Z",
                                 asked=[{"id": "q1", "q": "why", "a": "because", "at": 1, "at_a": 2}], sky="rain")
    for part in ('class="sky sky--rain"', 'class="capsule"', 'class="asks"', 'class="book"', 'class="board"',
                 'class="here"', '<div class="odo', 'class="since"', 'class="mood"', 'name name--shimmer name--halo',
                 'blk blk--h', 'blk blk--q', '--text:#F2F2F0;'):
        assert part in html, part


# ── v3.132: the page remembers you (in your browser, not ours) ───────────────────────────────────────────


def test_remember_puts_an_empty_shell_on_the_page_and_nothing_else():
    from app.profile_page import render_public_profile
    assert 'class="again"' not in render_public_profile(_cfg({}))
    html = render_public_profile(_cfg({"remember": True}))
    assert '<p class="again" data-again hidden' in html
    assert "your own browser remembers this" in html            # the page says whose memory it is
    assert "misa:seen:ren" in html                              # the key is per page, in localStorage
    # nothing about any visitor is rendered — the line is empty until their own browser fills it in
    body = html.split('<p class="again"', 1)[1].split("</p>", 1)[0]
    assert ">" not in body.replace('data-again hidden title="your own browser remembers this. misa.lol is not told, and clearing your site data forgets it.">', "")


def test_remember_is_free_and_survives_a_save(client, world):
    world.plan = None
    r = client.put("/api/v1/profile/me", json={"profile": {"username": "ren", "displayName": "ren"},
                                               "settings": {"remember": True}, "socials": [], "badges": [], "assets": {}})
    assert r.status_code == 200 and r.json()["profile"]["settings"]["remember"] is True
    assert "settings.remember" not in r.json().get("cleared", [])


def test_what_a_visitor_missed_is_datable_on_the_page():
    """v3.133: every answer, signature and drawing carries the second it appeared, so a returning visitor's own
    browser can work out what is new — the page itself never learns what anyone has seen."""
    from app.profile_page import render_public_profile
    html = render_public_profile(
        _cfg({"remember": True, "guestbook": True, "asks": True, "doodles": True}),
        signatures=[{"id": "g1", "name": "peach", "line": "hi", "at": 1757000000}],
        asked=[{"id": "q1", "q": "why", "a": "because", "at": 1756000000, "at_a": 1757100000}],
        drawings=[{"id": "d1", "at": 1757200000, "c": "chalk", "s": [[10, 10, 40, 40]]}])
    assert '<li class="slip" data-at="1757000000"' in html
    assert '<li class="qa" data-at="1757100000">' in html          # answered-at, not asked-at
    assert '<li class="tile" data-at="1757200000"' in html
    assert "is-new" in html                                        # the mark is styled, and applied by their browser only


# ── v3.134: the vigil — candles that burn themselves out ────────────────────────────────────────────────


def test_vigil_api_lights_one_and_the_page_draws_it(client, world):
    world.profiles[world.user.id]["settings"]["vigil"] = "12"
    r = client.post("/api/v1/vigil/ren")
    assert r.status_code == 201
    body = r.json()
    assert body["candle"]["burn"] == 12 * 3600 and 0 < body["candle"]["left"] <= 12 * 3600
    assert set(body["candle"]) == {"id", "lit", "burn", "left"}       # nothing about who lit it
    shelf = client.get("/api/v1/vigil/ren").json()
    assert shelf["burn"] == 12 * 3600 and len(shelf["lit"]) == 1

    from app.profile_page import render_public_profile
    html = render_public_profile(_cfg({"vigil": "12"}), candles=shelf["lit"])
    assert '<ul class="shelf" data-shelf>' in html and html.count('<li class="candle"') == 1
    assert "1 candle burning · they go out after 12 hours" in html    # singular, and it says how long
    assert 'data-vigil-light' in html

    # the owner can clear their own shelf; a visitor has no way to
    assert client.delete("/api/v1/me/vigil").status_code == 200
    assert client.get("/api/v1/vigil/ren").json()["lit"] == []


def test_vigil_one_candle_a_day_and_only_when_it_is_on(client, world):
    world.profiles[world.user.id]["settings"]["vigil"] = "6"
    assert client.post("/api/v1/vigil/ren").status_code == 201
    assert client.post("/api/v1/vigil/ren").status_code == 429        # same visitor, same day
    world.profiles[world.user.id]["settings"]["vigil"] = ""
    assert client.post("/api/v1/vigil/ren").status_code == 404
    assert client.get("/api/v1/vigil/ren").status_code == 404
    world.profiles[world.user.id]["settings"]["vigil"] = "99"         # not one of the three burn lengths
    assert client.get("/api/v1/vigil/ren").status_code == 404
    from app.profile_page import render_public_profile
    assert 'class="vigil"' not in render_public_profile(_cfg({"vigil": "99"}))
    assert 'class="vigil"' not in render_public_profile(_cfg({}))


def test_vigil_candles_go_out_on_their_own(world):
    import asyncio
    import time

    from app.core import vigil

    async def run():
        uid = "u-vigil"
        await vigil.light(uid, 3600, f"vg:{uid}:seen:a")
        await vigil.light(uid, 3600, f"vg:{uid}:seen:b")
        fresh = await vigil.lit(uid)
        # push one of them back in time so it is already spent
        r = vigil.get_dragonfly()
        member = f"gone|{int(time.time()) - 7200}|3600"
        await r.zadd(f"vg:{uid}", {member: int(time.time()) - 3600})
        return fresh, await vigil.lit(uid), await vigil.count(uid)

    fresh, still, n = asyncio.get_event_loop().run_until_complete(run())
    assert len(fresh) == 2 and n == 2
    assert [c["id"] for c in still] == [c["id"] for c in fresh]        # the spent one never shows up
    assert all(c["left"] > 0 for c in still)
    assert still[0]["lit"] <= still[1]["lit"]                          # oldest first — stubs on the left


def test_vigil_shelf_holds_a_limited_number(world):
    import asyncio

    from app.core import vigil

    async def run():
        uid = "u-vigil-many"
        for i in range(vigil.MAX + 20):
            await vigil.light(uid, 6 * 3600, f"vg:{uid}:seen:{i}")
        return await vigil.count(uid), await vigil.lit(uid), await vigil.lit(uid, 5)

    n, shown, five = asyncio.get_event_loop().run_until_complete(run())
    assert n == vigil.MAX
    assert len(shown) == vigil.SHOWN and len(five) == 5


def test_vigil_height_falls_with_the_time_left():
    from app.profile_page import render_public_profile
    html = render_public_profile(_cfg({"vigil": "24"}), candles=[
        {"id": "a", "lit": 1, "burn": 100, "left": 100},               # just lit — full height
        {"id": "b", "lit": 2, "burn": 100, "left": 25},                # nearly gone — a stub
        {"id": "c", "lit": 3, "burn": 100, "left": 0},                 # spent — not drawn at all
    ])
    assert '--h:1.000' in html and '--h:0.250' in html
    assert html.count('<li class="candle"') == 2
    assert "2 candles burning" in html                                 # plural, and the spent one is not counted


def test_vigil_empty_shelf_says_so_and_lighting_lands_in_the_replay(client, world):
    world.profiles[world.user.id]["settings"]["vigil"] = "24"
    world.profiles[world.user.id]["settings"]["replay"] = True
    from app.profile_page import render_public_profile
    html = render_public_profile(_cfg({"vigil": "24"}), candles=[])
    assert "the shelf is dark. nobody has lit one in 24 hours." in html
    assert '<ul class="shelf" data-shelf></ul>' in html                # still there, ready to fill

    assert client.post("/api/v1/vigil/ren").status_code == 201
    kinds = [e["k"] for e in client.get("/api/v1/me/replay").json()["visits"][0]["events"]]
    assert "light" in kinds


def test_vigil_is_free(client, world):
    world.plan = None
    r = client.put("/api/v1/profile/me", json={"profile": {"username": "ren", "displayName": "ren"},
                                               "settings": {"vigil": "12"}, "socials": [], "badges": [], "assets": {}})
    assert r.status_code == 200 and r.json()["profile"]["settings"]["vigil"] == "12"
    assert "settings.vigil" not in r.json().get("cleared", [])


# ── v3.135: the page has a back ─────────────────────────────────────────────────────────────────────────


def test_a_page_with_nothing_on_the_back_has_no_back():
    from app.profile_page import render_public_profile
    for settings in ({}, {"reverse": {}}, {"reverse": {"title": "  ", "text": "\n \n"}}, {"reverse": "liner notes"}):
        html = render_public_profile(_cfg(settings))
        assert '<div class="flip"' not in html and '<section class="card card--back"' not in html, settings
        assert 'class="dogear"' not in html, settings          # the styles are always in the sheet; the fold is not


def test_the_back_holds_writing_and_the_corner_turns_it_over():
    from app.profile_page import render_public_profile
    html = render_public_profile(_cfg({"reverse": {"title": "  liner   notes ", "text": "two\r\nlines\n\n  and a third  "}}))
    assert '<div class="flip" data-flip>' in html and '<section class="card card--back"' in html
    assert '<h2 class="back__title">liner notes</h2>' in html          # tidied
    assert html.count('<p class="back__p">') == 3                       # blank lines dropped, the rest kept apart
    assert '<p class="back__p">and a third</p>' in html
    assert 'data-flip-to="back" aria-expanded="false" aria-controls="card-back"' in html
    assert "turn the page over" in html and "turn it back" in html      # both ways say so to a screen reader


def test_the_back_can_be_nothing_but_blocks():
    from app.profile_page import render_public_profile
    html = render_public_profile(_cfg({"blocks": [
        {"id": "b1", "type": "heading", "text": "credits", "place": "back", "enabled": True},
        {"id": "b2", "type": "text", "text": "on the front", "place": "bottom", "enabled": True}]}))
    assert 'card--back' in html and '<h2 class="back__title">the other side</h2>' in html   # a name it gives itself
    back = html.split('card card--back', 1)[1]
    assert "credits" in back and "on the front" not in back             # each block went where it was sent
    assert "on the front" in html.split('card card--back', 1)[0]


def test_the_back_is_a_lifetime_perk(client, world):
    world.plan = None
    r = client.put("/api/v1/profile/me", json={"profile": {"username": "ren", "displayName": "ren"},
                                               "settings": {"reverse": {"title": "liner notes", "text": "hi"}},
                                               "socials": [], "badges": [], "assets": {}})
    assert r.status_code == 200
    assert r.json()["profile"]["settings"].get("reverse") in (None, {})
    assert "settings.reverse" in r.json().get("cleared", [])
    world.plan = "lifetime"
    r = client.put("/api/v1/profile/me", json={"profile": {"username": "ren", "displayName": "ren"},
                                               "settings": {"reverse": {"title": "liner notes", "text": "hi"}},
                                               "socials": [], "badges": [], "assets": {}})
    assert r.json()["profile"]["settings"]["reverse"]["title"] == "liner notes"


def test_the_back_takes_the_long_way_round_but_not_forever():
    from app.profile_page import render_public_profile
    html = render_public_profile(_cfg({"reverse": {"title": "x" * 80, "text": "y" * 1200}}))
    assert '<h2 class="back__title">' + "x" * 40 + "</h2>" in html
    assert "y" * 800 in html and "y" * 801 not in html


def test_the_back_escapes_what_is_written_on_it():
    from app.profile_page import render_public_profile
    html = render_public_profile(_cfg({"reverse": {"title": "<b>hi</b>", "text": "<script>alert(1)</script>"}}))
    assert "&lt;b&gt;hi&lt;/b&gt;" in html and "<script>alert(1)</script>" not in html


# ── v3.136: the tally — the page asks, and everyone sees the count ───────────────────────────────────────


def test_a_tally_needs_a_question_and_two_answers():
    from app.core.tally import clean
    assert clean(None) is None and clean("why") is None
    assert clean({"q": "  ", "options": ["a", "b"]}) is None
    assert clean({"q": "why?", "options": ["only one"]}) is None
    assert clean({"q": "why?", "options": ["a", "  ", None]}) is None            # blanks don't count
    q, opts, qid = clean({"q": "  which   one?  ", "options": ["Loud", "loud", "quiet", "b", "c", "d"]})
    assert q == "which one?"                                                     # whitespace tidied
    assert opts == ["Loud", "quiet", "b", "c"]                                   # the same answer twice is one; four is the most
    assert len(qid) == 10


def test_rewording_the_question_starts_a_clean_count():
    from app.core.tally import clean
    a = clean({"q": "which one?", "options": ["x", "y"]})[2]
    assert clean({"q": "which one?", "options": ["x", "y"]})[2] == a             # the same question is the same count
    assert clean({"q": "which one??", "options": ["x", "y"]})[2] != a            # a reworded one is a new count
    assert clean({"q": "which one?", "options": ["x", "z"]})[2] != a             # so is a changed answer


def test_tally_marks_are_fours_and_a_slash():
    from app.core.tally import MARKS_MAX, marks
    assert marks(0) == ""
    assert marks(3).count("<i>") == 3 and "mark--five" not in marks(3)
    assert marks(5).count("<i>") == 4 and marks(5).count("mark--five") == 1      # five is four and a slash
    assert marks(12).count('<b class="mark') == 3 and marks(12).count("mark--five") == 2   # 5 + 5 + 2
    assert marks(9999).count("<i>") == marks(MARKS_MAX).count("<i>")             # the number carries the rest


def test_tally_api_counts_one_answer_each(client, world):
    world.profiles[world.user.id]["settings"]["tally"] = {"q": "which one?", "options": ["the bus one", "the loud one"]}
    r = client.get("/api/v1/tally/ren")
    assert r.status_code == 200 and r.json() == {"q": "which one?", "options": ["the bus one", "the loud one"], "counts": [0, 0]}
    assert client.post("/api/v1/tally/ren", json={"choice": 1}).json()["counts"] == [0, 1]
    assert client.post("/api/v1/tally/ren", json={"choice": 0}).status_code == 429   # same visitor, same question
    assert client.get("/api/v1/tally/ren").json()["counts"] == [0, 1]
    assert client.post("/api/v1/tally/ren", json={"choice": 3}).status_code == 400   # not one of the answers
    assert client.post("/api/v1/tally/ren", json={"choice": 9}).status_code == 422   # not an answer at all


def test_a_page_asking_nothing_says_so(client, world):
    world.profiles[world.user.id]["settings"]["tally"] = {"q": "which one?", "options": ["only one"]}
    assert client.get("/api/v1/tally/ren").status_code == 404
    assert client.post("/api/v1/tally/ren", json={"choice": 0}).status_code == 404
    assert client.get("/api/v1/tally/nobody_here").status_code == 404
    from app.profile_page import render_public_profile
    assert 'class="tal"' not in render_public_profile(_cfg({}))
    assert 'class="tal"' not in render_public_profile(_cfg({"tally": {"q": "hi", "options": ["one"]}}))


def test_the_page_draws_the_question_and_the_answers_but_no_counts():
    """The counts are public, but they come from the API — nothing about them is baked into the HTML."""
    from app.profile_page import render_public_profile
    html = render_public_profile(_cfg({"tally": {"q": "which one should be the single?", "options": ["the bus one", "the loud one"]}}))
    assert '<h2 class="tal__title" id="tal-title">which one should be the single?</h2>' in html
    assert '<button class="tal__pick" type="button" data-tal-pick="0">the bus one</button>' in html
    assert '<span class="tal__marks" data-tal-marks="1" aria-hidden="true"></span>' in html    # empty until the page reads them
    assert "misa:tally:ren" in html                                                            # which one you picked stays in your browser


def test_a_changed_question_lets_everyone_answer_again(world):
    import asyncio

    from app.core import tally

    async def run():
        uid = "u-tally"
        first = tally.clean({"q": "which one?", "options": ["a", "b"]})
        again = tally.clean({"q": "which one, really?", "options": ["a", "b"]})
        key = tally.visitor_key(uid, first[2], "1.2.3.4", "ua", "salt")
        one = await tally.vote(uid, first[2], 0, 2, key)
        twice = await tally.vote(uid, first[2], 1, 2, key)
        newkey = tally.visitor_key(uid, again[2], "1.2.3.4", "ua", "salt")
        after = await tally.vote(uid, again[2], 1, 2, newkey)
        return one, twice, after, await tally.counts(uid, first[2], 2)

    one, twice, after, old = asyncio.get_event_loop().run_until_complete(run())
    assert one == [1, 0] and twice is None
    assert after == [0, 1]                                   # the new question starts at nothing
    assert old == [1, 0]                                     # and the old count is left where it was


# ── v3.137: see your page before you save it ────────────────────────────────────────────────────────────


def test_preview_draws_the_page_the_config_would_make(client, world):
    world.plan = "lifetime"
    draft = {"profile": {"username": "ren", "displayName": "ren", "description": "graveyard shift music."},
             "settings": {"accentColor": "#F00646", "guestbook": True, "tally": {"q": "which one?", "options": ["a", "b"]}},
             "socials": [{"id": "s1", "platform": "Spotify", "label": "new single", "value": "open.spotify.com/x", "enabled": True}],
             "badges": [], "assets": {}}
    r = client.post("/api/v1/profile/me/preview", json=draft)
    assert r.status_code == 200
    html = r.json()["html"]
    assert html.startswith("<!DOCTYPE html>") and "misa.lol/ren" in html
    assert 'class="book"' in html and 'class="tal"' in html          # the draft's own settings, not the saved ones
    assert "new single" in html
    assert r.json()["cleared"] == []


def test_preview_saves_nothing_and_counts_nothing(client, world):
    before = client.get("/api/v1/profile/me").json()["profile"]
    draft = {"profile": {"username": "ren", "displayName": "someone else"}, "settings": {"accentColor": "#00ff00"},
             "socials": [], "badges": [], "assets": {}}
    assert client.post("/api/v1/profile/me/preview", json=draft).status_code == 200
    after = client.get("/api/v1/profile/me").json()["profile"]
    assert after == before                                            # the stored profile is untouched
    assert client.get("/api/v1/me/replay").json()["visits"] == []     # and nothing was noted about it


def test_preview_applies_the_plan_to_a_copy(client, world):
    world.plan = None
    draft = {"profile": {"username": "ren", "displayName": "ren"},
             "settings": {"mood": True, "secret": {"word": "nightbus", "url": "https://example.com/b", "label": "b-side"}},
             "socials": [], "badges": [], "assets": {}}
    r = client.post("/api/v1/profile/me/preview", json=draft)
    assert r.status_code == 200
    assert set(r.json()["cleared"]) >= {"settings.mood", "settings.secret"}
    assert 'class="mood"' not in r.json()["html"]                     # drawn as it would really go up
    assert draft["settings"]["mood"] is True                          # and the caller's own body is left alone


def test_preview_needs_a_profile_and_an_account(client, world):
    assert client.post("/api/v1/profile/me/preview", json={"settings": {}}).status_code == 400
    world.user = None
    assert client.post("/api/v1/profile/me/preview", json={"profile": {"username": "ren"}}).status_code == 401


def test_the_live_page_and_the_preview_gather_the_same_parts(client, world):
    """v3.137 moved the guestbook/chalkboard/ask-box/vigil/sky reads into one place. Both callers use it."""
    import inspect

    from app import main as main_module
    from app.api.v1 import profile as profile_api
    from app.core import page_parts
    assert "gather" in inspect.getsource(main_module) and "page_parts" in inspect.getsource(main_module)
    assert "page_parts" in inspect.getsource(profile_api)
    src = inspect.getsource(page_parts)
    for word in ("guestbook", "doodles", "asks", "vigil", "sky", "nowplaying", "weather"):
        assert word in src, word
    body = src.split('"""', 2)[2]                                      # past the module docstring
    for write in ("presence_beat", "replay_note", "save_profile", "hincrby", "lpush", "zadd", ".set("):
        assert write not in body, write                                # gathering never writes anything


# ── v3.138: the draw — a line each, and the same one all day ─────────────────────────────────────────────


def test_the_deck_is_one_line_a_line():
    from app.core.draw import MAX, clean
    assert clean(None) == [] and clean("   \n\n ") == []
    assert clean("one\r\n\n  two   words  \nthree") == ["one", "two words", "three"]
    assert clean(["a", "", "b"]) == ["a", "b"]                       # a list works too
    assert len(clean("\n".join(str(i) for i in range(40)))) == MAX
    assert clean("x" * 400)[0] == "x" * 120


def test_the_same_visitor_gets_the_same_line_all_day():
    from app.core.draw import clean, pick
    deck = clean("one\ntwo\nthree\nfour\nfive")
    assert pick(deck, "aaaaaaaa", "2026-09-10") == pick(deck, "aaaaaaaa", "2026-09-10")
    assert pick(deck, "aaaaaaaa", "2026-09-10") in deck
    days = {pick(deck, "aaaaaaaa", f"2026-09-{d:02d}") for d in range(1, 29)}
    assert len(days) > 1                                             # a new day can deal a new line
    people = {pick(deck, f"{n:08x}", "2026-09-10") for n in range(200)}
    assert people == set(deck)                                       # over enough visitors, every line comes up
    assert pick([], "aaaaaaaa") == "" and pick(["only"], "zzz") == "only"


def test_the_page_shows_the_line_it_was_handed():
    from app.profile_page import render_public_profile
    html = render_public_profile(_cfg({"draw": "one\ntwo\nthree"}), drawn="two")
    assert '<h2 class="draw__title" id="draw-title">for you, today</h2>' in html
    assert '<p class="draw__card">two</p>' in html
    assert html.count('class="draw__card"') == 1                     # one line, not the deck
    for other in ("one", "three"):
        assert f'<p class="draw__card">{other}</p>' not in html      # the rest of the deck is not in the page


def test_no_deck_no_draw():
    from app.profile_page import render_public_profile
    assert 'class="draw"' not in render_public_profile(_cfg({}))
    assert 'class="draw"' not in render_public_profile(_cfg({"draw": "  \n "}), drawn="ignored")
    # a deck but no line handed over (a preview, say) still deals a steady one rather than showing nothing
    html = render_public_profile(_cfg({"draw": "one\ntwo"}))
    assert 'class="draw__card"' in html


def test_the_draw_escapes_the_line_and_is_a_lifetime_perk(client, world):
    from app.profile_page import render_public_profile
    html = render_public_profile(_cfg({"draw": "x"}), drawn="<script>alert(1)</script>")
    assert "<script>alert(1)</script>" not in html and "&lt;script&gt;" in html
    world.plan = None
    r = client.put("/api/v1/profile/me", json={"profile": {"username": "ren", "displayName": "ren"},
                                               "settings": {"draw": "one\ntwo"}, "socials": [], "badges": [], "assets": {}})
    assert "settings.draw" in r.json().get("cleared", [])


def test_the_draw_is_worked_out_at_render_and_never_stored(client, world):
    """Two visitors, one page: the gathering deals each of them their own line and writes nothing down."""
    import asyncio

    from app.core.page_parts import gather

    async def run():
        profile = {"settings": {"draw": "one\ntwo\nthree\nfour\nfive\nsix"}}
        seen = {(await gather("u-draw", profile, f"{n:08x}"))["drawn"] for n in range(60)}
        steady = (await gather("u-draw", profile, "aaaaaaaa"))["drawn"]
        again = (await gather("u-draw", profile, "aaaaaaaa"))["drawn"]
        from app.db.dragonfly import get_dragonfly
        keys = [k async for k in get_dragonfly().scan_iter(match="*", count=500)]
        return seen, steady, again, keys

    seen, steady, again, keys = asyncio.get_event_loop().run_until_complete(run())
    assert len(seen) > 1 and steady == again
    assert not [k for k in keys if "draw" in str(k)]                 # nothing about the draw is kept anywhere


# ── v3.139: everything on, again ────────────────────────────────────────────────────────────────────────


def test_the_page_reads_owner_first_then_visitors():
    """v3.139: the capsule and the draw are the owner talking to you; the guestbook, ask box, chalkboard,
    tally and vigil are what visitors do. They should not be interleaved."""
    from app.profile_page import render_public_profile
    html = render_public_profile(_cfg({
        "capsule": {"text": "for later", "at": "2099-12-24"}, "draw": "one\ntwo",
        "guestbook": True, "asks": True, "doodles": True, "vigil": "12",
        "tally": {"q": "which one?", "options": ["a", "b"]}}),
        signatures=[], asked=[], drawings=[], candles=[], drawn="one")
    order = [html.index(f'class="{c}"') for c in ("capsule", "draw", "book", "asks", "board", "tal", "vigil")]
    assert order == sorted(order), order


def test_everything_on_at_once_still_draws_every_part():
    """The composition pass, as a test: one page with all of it on, and nothing missing or clobbered."""
    from app.profile_page import render_public_profile
    html = render_public_profile(_cfg({
        "guestbook": True, "doodles": True, "asks": True, "presence": True, "since": True, "mood": True,
        "remember": True, "counterStyle": "odometer", "sky": "berlin", "usernameEffect": "shimmer",
        "usernameGlow": True, "supporterTag": True, "vigil": "24", "draw": "one\ntwo\nthree",
        "capsule": {"text": "for later", "at": "2099-12-24"},
        "tally": {"q": "which one?", "options": ["a", "b"]},
        "reverse": {"title": "liner notes", "text": "the drums are an sm57 in a stairwell."},
        "secret": {"word": "nightbus", "url": "https://example.com/b", "label": "the b-side"},
        "blocks": [{"id": "b1", "type": "heading", "text": "what i'm up to", "place": "top", "enabled": True},
                   {"id": "b2", "type": "quote", "text": "a laundrette in leipzig.", "place": "bottom", "enabled": True},
                   {"id": "b3", "type": "text", "text": "credits", "place": "back", "enabled": True}]}),
        views=12412, signatures=[{"id": "g1", "name": "peach", "line": "hi", "at": 1}], here=3, drawings=[],
        since="2026-07-01T10:00:00Z", asked=[{"id": "q1", "q": "why", "a": "because", "at": 1, "at_a": 2}],
        sky="rain", candles=[{"id": "c1", "lit": 1, "burn": 100, "left": 40}], drawn="two")
    for part in ('class="sky sky--rain"', 'class="capsule"', 'class="draw"', 'class="asks"', 'class="book"',
                 'class="board"', 'class="tal"', 'class="vigil"', 'class="here"', '<div class="odo',
                 'class="since"', 'class="mood"', 'name name--shimmer name--halo', 'class="flip"',
                 'card card--back', 'class="dogear"', 'blk blk--h', 'blk blk--q', '--text:#F2F2F0;'):
        assert part in html, part
    assert '<span class="sr-only">, supporter</span>' in html          # and the tag is spoken, not run together
    assert html.count('class="card') == 2                              # exactly two faces, front and back


# ── v3.142: the night shift ─────────────────────────────────────────────────────────────────────────────


def test_the_night_window_is_the_owners_clock():
    from datetime import datetime, timezone

    from app.profile_page import _night
    w = {"tz": "Europe/Berlin", "from": 23, "to": 5}                  # UTC+2 in september
    assert _night(w, datetime(2026, 9, 10, 0, 30, tzinfo=timezone.utc))[0] is True    # 2:30 am there
    assert _night(w, datetime(2026, 9, 10, 4, 30, tzinfo=timezone.utc))[0] is False   # 6:30 am there
    assert _night(w, datetime(2026, 9, 10, 21, 30, tzinfo=timezone.utc))[0] is True   # 11:30 pm there
    assert _night(w, datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc))[1] == "2:00 pm"
    # a window that doesn't wrap works the same way
    assert _night({"tz": "UTC", "from": 9, "to": 17}, datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc))[0] is True
    assert _night({"tz": "UTC", "from": 9, "to": 17}, datetime(2026, 9, 10, 20, 0, tzinfo=timezone.utc))[0] is False
    for bad in (None, "night", {}, {"tz": "not/a/zone"}, {"tz": "UTC", "from": 5, "to": 5}, {"tz": "UTC", "from": 99, "to": 2}, {"tz": "UTC", "from": "x", "to": 2}):
        assert _night(bad) is None, bad


def test_a_night_block_is_not_in_the_page_by_day():
    """The point of it: by day the words are never sent, so nobody reads them early from the source."""
    from datetime import datetime, timezone

    from app.profile_page import render_public_profile
    cfg = _cfg({"night": {"tz": "UTC", "from": 23, "to": 5},
                "blocks": [{"id": "b1", "type": "text", "text": "the b-side, unlisted", "place": "bottom", "enabled": True, "night": True},
                           {"id": "b2", "type": "text", "text": "always here", "place": "bottom", "enabled": True}]})

    import app.profile_page as pp
    real = pp._night
    try:
        pp._night = lambda raw, now=None: real(raw, datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc))
        day = render_public_profile(cfg)
        pp._night = lambda raw, now=None: real(raw, datetime(2026, 9, 10, 2, 0, tzinfo=timezone.utc))
        dark = render_public_profile(cfg)
    finally:
        pp._night = real

    assert "the b-side, unlisted" not in day and "always here" in day
    assert 'class="nightfall"' not in day and "card is-night" not in day
    assert "the b-side, unlisted" in dark and "always here" in dark
    assert 'class="nightfall">it’s 2:00 am where ren is. some of this is only here now.</p>' in dark
    assert "card is-night" in dark


def test_no_night_means_a_night_block_never_shows():
    from app.profile_page import render_public_profile
    html = render_public_profile(_cfg({"blocks": [
        {"id": "b1", "type": "text", "text": "the b-side, unlisted", "place": "bottom", "enabled": True, "night": True}]}))
    assert "the b-side, unlisted" not in html                          # no window set: it is never on
    assert 'class="nightfall"' not in html


def test_the_night_line_needs_a_night_block_to_say_anything():
    from datetime import datetime, timezone

    import app.profile_page as pp
    from app.profile_page import render_public_profile
    real = pp._night
    try:
        pp._night = lambda raw, now=None: real(raw, datetime(2026, 9, 10, 2, 0, tzinfo=timezone.utc))
        html = render_public_profile(_cfg({"night": {"tz": "UTC", "from": 23, "to": 5},
                                           "blocks": [{"id": "b1", "type": "text", "text": "always here", "place": "bottom", "enabled": True}]}))
    finally:
        pp._night = real
    assert "always here" in html and 'class="nightfall"' not in html    # nothing is held back, so nothing is claimed


def test_the_night_shift_is_a_lifetime_perk(client, world):
    world.plan = None
    r = client.put("/api/v1/profile/me", json={"profile": {"username": "ren", "displayName": "ren"},
                                               "settings": {"night": {"tz": "UTC", "from": 23, "to": 5}},
                                               "socials": [], "badges": [], "assets": {}})
    assert "settings.night" in r.json().get("cleared", [])


# ── v3.143: the archive — a page keeps what it used to be ───────────────────────────────────────────────


def test_every_save_shelves_the_page_it_replaced(client, world):
    def save(name):
        return client.put("/api/v1/profile/me", json={"profile": {"username": "ren", "displayName": name},
                                                      "settings": {"accentColor": "#F00646"}, "socials": [], "badges": [], "assets": {}})
    assert save("ren one").status_code == 200
    start = len(client.get("/api/v1/profile/me/archive").json()["days"])
    assert save("ren two").status_code == 200
    assert save("ren three").status_code == 200
    days = client.get("/api/v1/profile/me/archive").json()["days"]
    assert len(days) == start + 2 and days == sorted(days, reverse=True)   # one a save, newest first
    was = client.get(f"/api/v1/profile/me/archive/{days[0]}").json()["profile"]
    assert was["profile"]["displayName"] == "ren two"                      # the page the last save replaced
    assert client.get("/api/v1/profile/me/archive/1").status_code == 404


def test_saving_twice_without_changing_anything_shelves_nothing(world):
    import asyncio

    from app.core import archive

    async def run():
        cfg = {"profile": {"username": "ren"}, "settings": {"accentColor": "#F00646"}}
        first = await archive.keep("u-arch", cfg, now=1000)
        again = await archive.keep("u-arch", cfg, now=1001)
        moved = await archive.keep("u-arch", {"profile": {"username": "ren"}, "settings": {"accentColor": "#fff"}}, now=1002)
        return first, again, moved, await archive.shelf("u-arch")

    first, again, moved, days = asyncio.get_event_loop().run_until_complete(run())
    assert first is True and again is False and moved is True
    assert days == [1002, 1000]


def test_the_shelf_holds_a_limited_number(world):
    import asyncio

    from app.core import archive

    async def run():
        for i in range(archive.MAX + 8):
            await archive.keep("u-arch-many", {"n": i}, now=2000 + i)
        return await archive.shelf("u-arch-many")

    days = asyncio.get_event_loop().run_until_complete(run())
    assert len(days) == archive.MAX
    assert days[0] == 2000 + archive.MAX + 7 and min(days) > 2000        # the oldest fall off, newest kept


def test_putting_a_page_back_is_itself_undoable(client, world):
    for name in ("first", "second", "third"):
        client.put("/api/v1/profile/me", json={"profile": {"username": "ren", "displayName": name},
                                               "settings": {"accentColor": "#F00646"}, "socials": [], "badges": [], "assets": {}})
    days = client.get("/api/v1/profile/me/archive").json()["days"]
    want = next(d for d in days if client.get(f"/api/v1/profile/me/archive/{d}").json()["profile"]["profile"].get("displayName") == "first")
    r = client.post(f"/api/v1/profile/me/archive/{want}/restore")
    assert r.status_code == 200 and r.json()["profile"]["profile"]["displayName"] == "first"
    assert client.get("/api/v1/profile/me").json()["profile"]["profile"]["displayName"] == "first"
    after = client.get("/api/v1/profile/me/archive").json()["days"]
    assert len(after) == len(days) + 1                                   # what was there is on the shelf now
    back = client.get(f"/api/v1/profile/me/archive/{after[0]}").json()["profile"]
    assert back["profile"]["displayName"] == "third"                     # so the undo is undoable
    assert client.post("/api/v1/profile/me/archive/1/restore").status_code == 404


def test_a_restored_page_still_belongs_to_you_and_your_plan(client, world):
    world.plan = "lifetime"
    client.put("/api/v1/profile/me", json={"profile": {"username": "ren", "displayName": "ren"},
                                           "settings": {"mood": True}, "socials": [], "badges": [], "assets": {}})
    client.put("/api/v1/profile/me", json={"profile": {"username": "ren", "displayName": "ren"},
                                           "settings": {"mood": False}, "socials": [], "badges": [], "assets": {}})
    day = client.get("/api/v1/profile/me/archive").json()["days"][0]
    world.plan = None                                                     # they let Lifetime go since
    r = client.post(f"/api/v1/profile/me/archive/{day}/restore")
    assert r.status_code == 200
    assert r.json()["profile"]["settings"].get("mood") in (False, None)   # the plan is applied on the way back
    assert r.json()["profile"]["profile"]["username"] == "ren"


def test_the_archive_is_private_until_you_say_otherwise(client, world):
    assert client.get("/api/v1/profile/me/archive").status_code == 200
    world.user = None
    assert client.get("/api/v1/profile/me/archive").status_code == 401
    assert client.post("/api/v1/profile/me/archive/1/restore").status_code == 401


def test_the_bar_says_what_you_are_reading():
    from app.profile_page import render_public_profile
    html = render_public_profile(_cfg({}), was_at=1757462400)                 # 10 sep 2025
    assert '<p class="wasat" role="status">' in html and "as it was on <b>10 sep 2025</b>" in html
    assert '<a href="/ren">back to now</a>' in html
    assert '<p class="wasat"' not in render_public_profile(_cfg({}))


# ── v3.144: neighbours — pages that name each other ─────────────────────────────────────────────────────


def test_a_neighbour_list_is_tidied_and_capped():
    from app.core.neighbours import MAX, clean
    assert clean(None) == [] and clean("peach") == []
    assert clean([" PEACH ", "@void", "misa.lol/lune", "peach", "", None, "not a name!"]) == ["peach", "void", "lune"]
    assert clean(["ren", "peach"], mine="ren") == ["peach"]              # you can't name yourself
    assert len(clean([f"n{i}" for i in range(20)])) == MAX


def test_only_pages_that_name_each_other_show(world):
    import asyncio

    from app.core import neighbours

    class U:
        def __init__(self, uid, suspended=False):
            self.id, self.currently_suspended = uid, suspended

    pages = {
        "peach": (U("u-peach"), {"profile": {"displayName": "peach"}, "settings": {"neighbours": ["ren"], "accentColor": "#ff6ea9"}}),
        "void":  (U("u-void"),  {"profile": {"displayName": "void"},  "settings": {"neighbours": ["someone-else"]}}),
        "lune":  (U("u-lune", suspended=True), {"profile": {}, "settings": {"neighbours": ["ren"]}}),
        "hex":   (U("u-hex"),   {"profile": {"displayName": "hex"},   "settings": {"neighbours": ["REN"], "accentColor": "nope"}}),
    }

    async def find_user(username=None):
        return pages.get(username, (None, None))[0]

    async def get_profile(uid):
        return next((p for u, p in pages.values() if u and u.id == uid), None)

    async def run():
        got = await neighbours.resolve("u-ren", "ren", ["peach", "void", "lune", "hex", "nobody"], find_user, get_profile)
        return got, await neighbours.peek("u-ren")

    got, cached = asyncio.get_event_loop().run_until_complete(run())
    assert [n["username"] for n in got] == ["peach", "hex"]              # void didn't name back; lune is suspended
    assert got[0]["accent"] == "#ff6ea9" and got[1]["accent"] == ""      # a colour that isn't one is dropped
    assert cached == got                                                 # and the answer is cached


def test_the_page_draws_only_what_resolved(world):
    from app.profile_page import render_public_profile
    cfg = _cfg({"neighbours": ["peach", "void"]})
    empty = render_public_profile(cfg)
    assert 'class="nb"' in empty and "nobody has named this page back yet" in empty
    assert "/peach" not in empty and "/void" not in empty                # a name alone puts nothing on the page

    html = render_public_profile(cfg, neighbours=[{"username": "peach", "name": "peach", "accent": "#ff6ea9"}])
    assert '<a href="/peach" style="--nb:#ff6ea9">' in html and "misa.lol/peach" in html
    assert "/void" not in html
    assert 'class="nb"' not in render_public_profile(_cfg({}))


def test_the_neighbours_api_needs_both_sides(client, world):
    world.profiles[world.user.id]["settings"]["neighbours"] = ["peach"]
    r = client.get("/api/v1/neighbours/ren")
    assert r.status_code == 200 and r.json()["neighbours"] == []         # peach isn't a real page here
    world.profiles[world.user.id]["settings"]["neighbours"] = []
    assert client.get("/api/v1/neighbours/ren").json()["neighbours"] == []
    assert client.get("/api/v1/neighbours/nobody_here").status_code == 404
    assert client.get("/api/v1/neighbours/NOT A NAME").status_code == 404


def test_neighbours_are_free(client, world):
    world.plan = None
    r = client.put("/api/v1/profile/me", json={"profile": {"username": "ren", "displayName": "ren"},
                                               "settings": {"neighbours": ["peach"]}, "socials": [], "badges": [], "assets": {}})
    assert r.status_code == 200 and r.json()["profile"]["settings"]["neighbours"] == ["peach"]
    assert "settings.neighbours" not in r.json().get("cleared", [])


# ── v3.146: the moon ────────────────────────────────────────────────────────────────────────────────────


def test_the_moon_runs_through_its_cycle():
    from datetime import datetime, timedelta, timezone

    from app.core.moon import SYNODIC, phase
    new_moon = datetime(2026, 9, 11, 3, 27, tzinfo=timezone.utc)
    seen = []
    for i in range(8):
        where, lit, name, waxing = phase(new_moon + timedelta(days=SYNODIC * i / 8))
        seen.append((round(lit, 2), name, waxing))
    lits = [x[0] for x in seen]
    assert lits[0] < 0.02 and lits[4] > 0.98                          # new, then full, half a month later
    assert lits[:5] == sorted(lits[:5]) and lits[4:] == sorted(lits[4:], reverse=True)
    assert [x[2] for x in seen] == [False, True, True, True, True, False, False, False]
    assert [x[1] for x in seen] == ["new moon", "waxing crescent", "first quarter", "waxing gibbous",
                                    "full moon", "waning gibbous", "last quarter", "waning crescent"]
    # and it is the same moon a whole cycle later
    a = phase(new_moon + timedelta(days=3))
    b = phase(new_moon + timedelta(days=3 + SYNODIC))
    assert abs(a[1] - b[1]) < 0.01 and a[2] == b[2]


def test_the_drawing_is_one_path_and_says_what_it_is():
    from datetime import datetime, timedelta, timezone

    from app.core.moon import SYNODIC, svg
    new_moon = datetime(2026, 9, 11, 3, 27, tzinfo=timezone.utc)
    crescent, label = svg(new_moon + timedelta(days=3))
    assert crescent.count("<path") == 1 and crescent.count("<circle") == 1   # the dark disc, then the lit part
    assert "waxing crescent" in label and "% lit" in label
    assert 'role="img"' in crescent and "tonight’s moon:" in crescent
    full, flabel = svg(new_moon + timedelta(days=SYNODIC / 2))
    assert full.count("<path") == 0 and flabel == "full moon"                # a full moon is just a disc
    new, nlabel = svg(new_moon)
    assert new.count("<path") == 0 and nlabel == "new moon"


def test_a_page_wears_the_moon_only_when_asked(client, world):
    from app.profile_page import render_public_profile
    assert 'class="moonw' not in render_public_profile(_cfg({}))
    html = render_public_profile(_cfg({"moon": True}))
    assert 'class="moonw' in html and 'class="moon"' in html
    assert "tonight’s moon:" in html
    world.plan = None
    r = client.put("/api/v1/profile/me", json={"profile": {"username": "ren", "displayName": "ren"},
                                               "settings": {"moon": True}, "socials": [], "badges": [], "assets": {}})
    assert r.json()["profile"]["settings"]["moon"] is True                   # free
    assert "settings.moon" not in r.json().get("cleared", [])
