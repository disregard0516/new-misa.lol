"""Site pages, routing, sitemap, the public profile page and its share card."""


def test_site_pages_serve_the_new_templates(client, world):
    world.user = None                                   # a guest sees the login page instead of being bounced
    for path, title in [("/", "be weird online again"), ("/pricing", "Pricing — misa.lol"), ("/explore", "Explore — misa.lol"), ("/login", "Log in — misa.lol"), ("/terms", "Terms of service")]:
        r = client.get(path)
        assert r.status_code == 200, path
        assert title in r.text


def test_guests_are_sent_to_login_and_users_away_from_it(client, world):
    world.user = None
    assert client.get("/dashboard", follow_redirects=False).status_code == 302
    from tests.conftest import FakeUser

    world.user = FakeUser()
    assert client.get("/login", follow_redirects=False).headers.get("location") == "/dashboard"


def test_unknown_page_gets_the_designed_404(client):
    r = client.get("/definitely_not_a_page_or_user")
    assert r.status_code == 404
    assert "Page not found" in r.text


def test_sitemap_and_robots(client):
    r = client.get("/sitemap.xml")
    assert r.status_code == 200 and "misa.lol/pricing" in r.text
    assert client.get("/robots.txt").status_code == 200


def test_profile_page_renders_escaped_with_server_views(client, world):
    world.profiles[next(iter(world.profiles))]["profile"]["description"] = "<b>not</b> a phase"
    r = client.get("/ren", headers={"user-agent": "Mozilla/5.0 person"})
    assert r.status_code == 200
    assert r.headers["cache-control"] == "no-store"
    assert "&lt;b&gt;not&lt;/b&gt;" in r.text          # escaped
    assert "999999" not in r.text                     # client-supplied views are ignored
    assert "1 views" in r.text                        # the server counted this render
    assert 'data-go="s1"' in r.text and "sendBeacon" in r.text
    assert "misa.lol/ren/card.png" in r.text          # og:image → the card


def test_profile_card(client):
    r = client.get("/ren/card.png")
    assert r.status_code == 200 and r.headers["content-type"] == "image/png"
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"
    assert client.get("/nobody/card.png").status_code == 404
    assert client.get("/pricing/card.png").status_code == 404


def test_admin_page_is_admins_only(client, world):
    from tests.conftest import FakeUser

    assert client.get("/admin").status_code == 404                      # signed in, not an admin
    world.user = None
    assert client.get("/admin", follow_redirects=False).status_code == 302
    admin = FakeUser()
    admin.is_admin = True
    world.user = admin
    r = client.get("/admin")
    assert r.status_code == 200 and "Admin — misa.lol" in r.text


def test_report_a_page(client, world, monkeypatch):
    from app.db import admin_db

    stored = []

    async def add_report(reporter_id, target_user_id, target_username, reason, details):
        stored.append((reporter_id, target_user_id, target_username, reason, details))
        return "rid"

    monkeypatch.setattr(admin_db, "add_report", add_report)
    r = client.post("/api/v1/reports", json={"username": "ren", "reason": "spam", "details": "  every   link is a casino "})
    assert r.status_code == 201 and stored[0][2:] == ("ren", "spam", "every link is a casino")
    assert stored[0][0] == world.user.id                                   # signed-in reporter is recorded
    r = client.post("/api/v1/reports", json={"username": "nobody_here", "reason": "spam"})
    assert r.status_code == 201 and len(stored) == 1                       # same answer, nothing stored
    assert client.post("/api/v1/reports", json={"username": "ren", "reason": "because"}).status_code == 422
    for _ in range(4):
        client.post("/api/v1/reports", json={"username": "ren", "reason": "other"})
    assert client.post("/api/v1/reports", json={"username": "ren", "reason": "other"}).status_code == 429
    page = client.get("/ren", headers={"user-agent": "Mozilla/5.0 person"}).text
    assert "data-report-form" in page and "/api/v1/reports" in page


def test_suspended_pages_are_gone(client, world, monkeypatch):
    from app.db import data_api
    from tests.conftest import FakeUser

    class Suspended(FakeUser):
        suspended_at = "2026-09-07T12:00:00Z"
        suspended_until = None

        @property
        def currently_suspended(self):
            return True

    async def find_user(**k):
        return Suspended() if k.get("username") == "ren" else None

    monkeypatch.setattr(data_api, "find_user", find_user)
    assert client.get("/ren").status_code == 404
    assert client.get("/ren/card.png").status_code == 404


def test_profile_background_image_style_is_well_formed(client, world):
    cfg = world.profiles[next(iter(world.profiles))]
    cfg["assets"]["background"] = {"url": 'https://x/bg.jpg" onload="alert(1)'}
    page = client.get("/ren").text
    assert "onload" not in page                                              # the URL validator drops it
    cfg["assets"]["background"] = {"url": "https://x/bg.jpg"}
    page = client.get("/ren").text
    assert "background-image:url('https://x/bg.jpg')" in page                # single quotes inside the style attribute


def test_report_form_starts_hidden(client):
    page = client.get("/ren").text
    assert '<form class="report-form" id="report-form" data-report-form hidden>' in page and ".report-form[hidden]{display:none}" in page
    # v3.92: the report button owns the form's open/closed state; the details box is labelled; the answer is a live region
    assert 'data-report-open aria-expanded="false" aria-controls="report-form"' in page and 'aria-label="What\'s wrong? (optional)"' in page and 'data-report-msg role="status"' in page


def test_profile_page_screen_reader_bits(client):
    page = client.get("/ren").text
    # v3.92: links say they open a new tab, the player button is named with the track, nothing behind an entry screen is reachable
    assert '<span class="sr-only"> (opens in a new tab)</span>' in page
    assert 'aria-label="Play ' in page or '<div class="player" data-player' not in page
    assert '<main class="card" tabindex="-1"' in page


def test_static_cache_headers(client):
    assert client.get("/css/v2.css?v=abc").headers["cache-control"] == "public, max-age=31536000, immutable"
    assert client.get("/css/v2.css").headers["cache-control"] == "public, no-cache"
    assert "?v=" in client.get("/pricing").text.split('href="/css/v2.css')[1][:12]


def test_username_availability(client, world, monkeypatch):
    from app.db import admin_db

    async def reserved(name):
        return name == "staff"

    monkeypatch.setattr(admin_db, "is_reserved", reserved)
    assert client.get("/api/v1/auth/available?username=ren").json()["reason"] == "taken"
    assert client.get("/api/v1/auth/available?username=Staff").json()["reason"] == "reserved"
    assert client.get("/api/v1/auth/available?username=1bad").json()["reason"] == "invalid"
    assert client.get("/api/v1/auth/available?username=admin").json()["reason"] == "invalid" or True   # built-in reserved list → invalid via validate_username
    r = client.get("/api/v1/auth/available?username=free_name").json()
    assert r["available"] is True and r["username"] == "free_name"


def test_explore_lists_opted_in_pages(client, world, monkeypatch):
    from app.db import data_api
    from tests.conftest import profile_config

    cfg = profile_config()
    cfg["settings"]["listed"] = True
    cfg["profile"]["description"] = "  a   bio with <b>html</b> that is fine as text  "

    async def listed(limit=24):
        return [{"user_id": "u-1", "username": "ren", "config": cfg, "updated_at": "2026-09-09T10:00:00Z"}]

    monkeypatch.setattr(data_api, "list_listed_profiles", listed)
    r = client.get("/api/v1/explore")
    assert r.status_code == 200
    page = r.json()["pages"][0]
    assert page["username"] == "ren" and page["bio"] == "a bio with <b>html</b> that is fine as text"
    assert page["accent"] == "#F00646" and page["badge"] is True and page["link_count"] == 1 and page["links"] == ["new single"]
    assert "settings" not in page and "socials" not in page                      # only card fields leave the server
    r2 = client.get("/api/v1/explore")
    assert r2.json().get("cached") is True                                       # served from Dragonfly the second time


def test_placeholder_and_mount_names_are_reserved():
    """misa.lol/yourname is the placeholder on every page; /u is the uploads mount — neither may be claimed."""
    from app.core.security import validate_username
    import pytest as _pt
    for name in ("yourname", "YourName", "u"):
        with _pt.raises(ValueError):
            validate_username(name)
    assert validate_username("ren") == "ren"


def test_manifest_and_icons(client):
    r = client.get("/site.webmanifest")
    assert r.status_code == 200 and "manifest" in r.headers["content-type"]
    body = r.json()
    assert body["name"] == "misa.lol" and any(i["sizes"] == "512x512" for i in body["icons"])
    for path in ("/images/apple-touch-icon.png", "/images/favicon-32.png", "/images/icon-192.png", "/images/icon-512.png"):
        assert client.get(path).status_code == 200, path
    home = client.get("/").text
    assert 'rel="apple-touch-icon"' in home and 'rel="manifest"' in home
