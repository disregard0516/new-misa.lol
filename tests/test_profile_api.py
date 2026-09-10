"""PUT /api/v1/profile/me: shape, badges from the server, plan gating, server-owned views."""
from tests.conftest import profile_config


def test_save_requires_the_bare_profile_config(client):
    r = client.put("/api/v1/profile/me", json={"profile": {"username": "someone_else", "displayName": "x"}})
    assert r.status_code == 400 and "does not match" in r.json()["detail"]


def test_free_plan_loses_paid_cosmetics_and_self_declared_badges(client, world):
    r = client.put("/api/v1/profile/me", json=profile_config())
    assert r.status_code == 200
    saved, cleared = r.json()["profile"], r.json()["cleared"]
    assert saved["assets"]["backgroundVideo"]["url"] is None
    assert saved["settings"]["usernameEffect"] == "None"
    assert saved["settings"]["entryScreen"] is False
    assert "assets.backgroundVideo.url" in cleared and "assets.cursor.url" in cleared
    assert [b["id"] for b in saved["badges"]] == ["verified"]           # "Staff" from the client is gone
    assert saved["profile"]["views"] == 0                              # not 999999


def test_lifetime_keeps_video_but_not_the_cursor(client, world):
    world.plan = "lifetime"
    r = client.put("/api/v1/profile/me", json=profile_config())
    saved = r.json()["profile"]
    assert saved["assets"]["backgroundVideo"]["url"] == "https://x/loop.mp4"
    assert saved["assets"]["cursor"]["url"] is None
    assert r.json()["cleared"] == ["assets.cursor.url", "settings.usernameGlow"] or "assets.cursor.url" in r.json()["cleared"]


def test_supporter_keeps_everything(client, world):
    world.plan = "supporter"
    r = client.put("/api/v1/profile/me", json=profile_config())
    assert r.json()["cleared"] == []
    assert r.json()["profile"]["assets"]["cursor"]["url"] == "https://x/c.png"


def test_badge_show_hide_choice_is_kept_for_owned_badges(client, world):
    cfg = profile_config(badges=[{"id": "verified", "enabled": False}])
    r = client.put("/api/v1/profile/me", json=cfg)
    assert r.json()["profile"]["badges"][0]["enabled"] is False


def test_admin_db_down_keeps_previous_badges_and_skips_gating(client, world):
    world.plan = "supporter"
    client.put("/api/v1/profile/me", json=profile_config())          # stores verified badge
    world.admin_down = True
    r = client.put("/api/v1/profile/me", json=profile_config(badges=[{"id": "staff", "enabled": True, "owned": True}]))
    assert r.status_code == 200
    assert [b["id"] for b in r.json()["profile"]["badges"]] == ["verified"]
    assert r.json()["cleared"] == []


def test_me_carries_plan_and_badges(client, world):
    world.plan = "lifetime"
    me = client.get("/api/v1/me").json()
    assert me["plan"] == "lifetime" and me["badges"][0]["id"] == "verified"
    world.admin_down = True
    assert client.get("/api/v1/me").json()["plan"] == "free"


def test_badge_toggle(client, world):
    assert client.patch("/api/v1/me/badges/verified", json={"enabled": False}).status_code == 200
    assert world.badges[0]["enabled"] is False
    assert client.patch("/api/v1/me/badges/nope", json={"enabled": True}).status_code == 404


def test_delete_account(client, world, monkeypatch, tmp_path):
    from app.db import data_api
    from app.core import sessions
    from app.api.v1 import users as users_api

    calls = []

    async def delete_user(uid):
        calls.append(uid)
        return True

    async def destroy(token):
        calls.append("session")

    monkeypatch.setattr(data_api, "delete_user", delete_user)
    monkeypatch.setattr(users_api, "destroy_session", destroy)
    r = client.request("DELETE", "/api/v1/me", json={"confirm": "nope"})
    assert r.status_code == 400 and not calls
    world.user.password_hash = None                                        # oauth-only account: no password needed
    r = client.request("DELETE", "/api/v1/me", json={"confirm": "delete"})
    assert r.status_code == 200 and calls == [world.user.id, "session"]


def test_delete_account_needs_the_password(client, world, monkeypatch):
    from app.core.security import hash_password
    from app.db import data_api

    async def delete_user(uid):
        return True

    monkeypatch.setattr(data_api, "delete_user", delete_user)
    world.user.password_hash = hash_password("correct horse")
    assert client.request("DELETE", "/api/v1/me", json={"confirm": "delete", "password": "wrong"}).status_code == 403
    assert client.request("DELETE", "/api/v1/me", json={"confirm": "delete", "password": "correct horse"}).status_code == 200


def test_set_and_change_password(client, world, monkeypatch):
    from app.core.security import hash_password, verify_password
    from app.db import data_api

    saved = {}

    async def update_user(uid, **fields):
        saved.update(fields)
        return world.user

    monkeypatch.setattr(data_api, "update_user", update_user)
    world.user.password_hash = None                                              # oauth-only account sets one
    assert client.patch("/api/v1/me/password", json={"new_password": "correct horse"}).status_code == 200
    assert verify_password(saved["password_hash"], "correct horse")
    world.user.password_hash = hash_password("correct horse")
    assert client.patch("/api/v1/me/password", json={"new_password": "battery staple"}).status_code == 403          # current required
    assert client.patch("/api/v1/me/password", json={"current_password": "wrong", "new_password": "battery staple"}).status_code == 403
    assert client.patch("/api/v1/me/password", json={"current_password": "correct horse", "new_password": "short"}).status_code == 422
    assert client.patch("/api/v1/me/password", json={"current_password": "correct horse", "new_password": "battery staple"}).status_code == 200
    assert verify_password(saved["password_hash"], "battery staple")


def test_admin_can_delete_a_user(client, world, monkeypatch):
    from app.db import data_api
    from app.api.v1 import admin as admin_api
    from tests.conftest import FakeUser

    class Other(FakeUser):
        id = "22222222-2222-2222-2222-222222222222"
        username = "spammer"

    calls = []

    async def get_user(uid):
        return Other() if uid == Other.id else None

    async def delete_user(uid):
        calls.append(uid)
        return True

    monkeypatch.setattr(data_api, "get_user", get_user)
    monkeypatch.setattr(data_api, "delete_user", delete_user)
    assert client.delete(f"/api/v1/admin/users/{Other.id}").status_code == 403          # not an admin
    admin = FakeUser()
    admin.is_admin = True
    world.user = admin
    monkeypatch.setattr(admin_api, "get_user_from_request", lambda *a, **k: _co(admin))
    assert client.delete(f"/api/v1/admin/users/{admin.id}").status_code == 400           # not yourself
    assert client.delete(f"/api/v1/admin/users/{Other.id}").status_code == 200 and calls == [Other.id]
    assert client.delete("/api/v1/admin/users/33333333-3333-3333-3333-333333333333").status_code == 404


async def _co(value):
    return value


def test_rename_follows_into_the_saved_profile(client, world, monkeypatch):
    """PATCH /me/username must update profile.username in the stored config — the public page and the
    share card read the name from there (v3.36)."""
    from app.db import admin_db

    async def not_reserved(name):
        return False

    monkeypatch.setattr(admin_db, "is_reserved", not_reserved)
    assert world.profiles[world.user.id]["profile"]["username"] == "ren"
    r = client.patch("/api/v1/me/username", json={"username": "lune"})
    assert r.status_code == 200, r.text
    assert world.profiles[world.user.id]["profile"]["username"] == "lune"
