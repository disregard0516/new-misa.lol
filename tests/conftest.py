"""Test fixtures: the app boots with every external service stubbed — no Postgres, no data API, no Dragonfly (a fake one).

Run:  pip install -r requirements-dev.txt && python -m pytest
"""
from __future__ import annotations

import io
import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MISA_DATA_API_URL", "http://127.0.0.1:9")
os.environ.setdefault("MISA_DATA_API_KEY", "test-key")
os.environ.setdefault("MISA_DRAGONFLY_URL", "redis://127.0.0.1:9/0")
os.environ["MISA_UPLOAD_DIR"] = tempfile.mkdtemp(prefix="misa-uploads-")

import fakeredis.aioredis as fakeredis  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import admin_db, data_api, dragonfly  # noqa: E402


class FakeUser:
    id = "11111111-1111-1111-1111-111111111111"
    username = "ren"
    display_name = "ren"
    email = "ren@example.com"
    is_admin = False
    currently_suspended = False
    password_hash = None
    created_at = (__import__("datetime").datetime.now(__import__("datetime").timezone.utc) - __import__("datetime").timedelta(days=45)).strftime("%Y-%m-%dT%H:%M:%SZ")  # a page 45 days old

    def to_public_dict(self):
        return {"id": self.id, "email": self.email, "username": self.username, "display_name": self.display_name, "providers": {"email": True}}


def profile_config(**over):
    cfg = {
        "profile": {"username": "ren", "displayName": "ren", "description": "not a phase.", "views": 999999},
        "settings": {"accentColor": "#F00646", "showViews": True, "showSocials": True, "usernameEffect": "Shimmer", "entryScreen": True},
        "assets": {"avatar": {"url": None}, "backgroundVideo": {"url": "https://x/loop.mp4"}, "cursor": {"url": "https://x/c.png"}},
        "socials": [{"id": "s1", "platform": "Spotify", "label": "new single", "value": "open.spotify.com/x", "enabled": True, "displayMode": "link"}],
        "badges": [{"id": "staff", "name": "Staff", "enabled": True, "owned": True}],
    }
    cfg.update(over)
    return cfg


class World:
    """Mutable state the stubs read: who is signed in, what's stored, which plan and badges the admin DB says."""

    def __init__(self):
        self.user: FakeUser | None = FakeUser()
        self.profiles: dict[str, dict] = {FakeUser.id: profile_config()}
        self.plan: str | None = None                      # None = free
        self.badges: list[dict] = [{"id": "verified", "name": "Verified", "description": "the blue check", "color": "#3b82f6", "enabled": True}]
        self.admin_down = False


@pytest.fixture()
def world(monkeypatch):
    w = World()

    async def noop(*a, **k):
        return None

    async def find_user(**k):
        return FakeUser() if k.get("username") == "ren" else None

    async def get_profile(uid):
        return w.profiles.get(uid)

    async def save_profile(uid, cfg):
        w.profiles[uid] = cfg
        return cfg

    async def update_user(uid, **fields):
        return FakeUser()

    async def current_user(*a, **k):
        return w.user

    async def user_plan(uid):
        if w.admin_down:
            raise RuntimeError("admin database is not initialised")
        return {"plan": w.plan, "expires_at": None} if w.plan else None

    async def user_badges(uid):
        if w.admin_down:
            raise RuntimeError("admin database is not initialised")
        return list(w.badges)

    async def set_badge_enabled(uid, badge_id, enabled):
        for b in w.badges:
            if b["id"] == badge_id:
                b["enabled"] = enabled
                return True
        return False

    for mod in (data_api,):
        monkeypatch.setattr(mod, "init_data_api", noop)
        monkeypatch.setattr(mod, "close_data_api", noop)
        monkeypatch.setattr(mod, "find_user", find_user)
        monkeypatch.setattr(mod, "get_profile", get_profile)
        monkeypatch.setattr(mod, "save_profile", save_profile)
        monkeypatch.setattr(mod, "update_user", update_user)
    monkeypatch.setattr(admin_db, "user_plan", user_plan)
    monkeypatch.setattr(admin_db, "user_badges", user_badges)
    monkeypatch.setattr(admin_db, "set_badge_enabled", set_badge_enabled)
    monkeypatch.setattr(admin_db, "init_admin_db", noop)
    monkeypatch.setattr(admin_db, "close_admin_db", noop)
    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(dragonfly, "_client", fake)
    monkeypatch.setattr(dragonfly, "init_dragonfly", lambda url: fake)
    monkeypatch.setattr(dragonfly, "close_dragonfly", noop)

    import app.main as main_module
    from app.api.v1 import asks as asks_api, vigil as vigil_api, doodles as doodles_api, guestbook as guestbook_api, linkcheck as linkcheck_api, profile as profile_api, reports as reports_api, uploads as uploads_api, replay as replay_api, users as users_api
    from app.core import sessions

    monkeypatch.setattr(main_module, "init_data_api", noop)
    monkeypatch.setattr(main_module, "close_data_api", noop)
    monkeypatch.setattr(main_module, "init_admin_db", noop)
    monkeypatch.setattr(main_module, "close_admin_db", noop)
    monkeypatch.setattr(main_module, "init_dragonfly", lambda url: fake)
    monkeypatch.setattr(main_module, "close_dragonfly", noop)
    monkeypatch.setattr(main_module, "get_user_from_request", current_user)
    monkeypatch.setattr(sessions, "get_user_from_request", current_user)
    for mod in (profile_api, reports_api, uploads_api, users_api, guestbook_api, doodles_api, linkcheck_api, replay_api, asks_api, vigil_api):
        monkeypatch.setattr(mod, "get_user_from_request", current_user)
    w.app = main_module.app
    return w


@pytest.fixture()
def client(world):
    with TestClient(world.app) as c:
        yield c


def png_bytes(size=(64, 64)):
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", size, (240, 6, 70)).save(buf, "PNG")
    return buf.getvalue()
