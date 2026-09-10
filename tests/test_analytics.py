"""Views, referrers, clicks — counted on the server, deduped, bots skipped."""


def test_views_dedupe_visitors_and_skip_bots(client):
    person = {"user-agent": "Mozilla/5.0 person", "referer": "https://t.co/abc"}
    for _ in range(3):
        client.get("/ren", headers=person)
    client.get("/ren", headers={"user-agent": "Mozilla/5.0 other", "x-forwarded-for": "10.0.0.2", "referer": "https://discord.com/channels/x"})
    client.get("/ren", headers={"user-agent": "Discordbot/2.0 (+https://discordapp.com)"})
    stats = client.get("/api/v1/me/stats").json()
    assert stats["views"] == 2 and stats["today"] == 2 and stats["week"] == 2
    assert dict(stats["referrers"]) == {"t.co": 1, "discord.com": 1}
    assert len(stats["daily"]) == 14


def test_click_beacon_is_public_and_labelled(client):
    assert client.post("/api/v1/hit/ren/s1").status_code == 204
    assert client.post("/api/v1/hit/ren/s1").status_code == 204
    assert client.post("/api/v1/hit/nobody/s1").status_code == 204       # never reveals whether a name exists
    stats = client.get("/api/v1/me/stats").json()
    assert stats["clicks"][0] == ["s1", "new single", 2]


def test_stats_degrade_when_dragonfly_is_down(client, monkeypatch):
    from app.core import analytics

    async def boom(uid, days=14):
        raise RuntimeError("down")

    monkeypatch.setattr("app.api.v1.users.analytics_stats", boom)
    stats = client.get("/api/v1/me/stats").json()
    assert stats["unavailable"] is True and stats["views"] == 0


def test_click_table_is_capped(client):
    for i in range(80):
        client.post(f"/api/v1/hit/ren/junk{i}")
    stats = client.get("/api/v1/me/stats").json()
    from app.core.analytics import MAX_CLICK_IDS

    assert len(stats["clicks"]) <= 20                      # the API returns the top 20
    assert client.post("/api/v1/hit/ren/junk0").status_code == 204   # existing ids still count
