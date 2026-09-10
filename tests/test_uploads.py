"""POST/GET/DELETE /api/v1/uploads: plan gate, sniffing, limits, traversal."""
from tests.conftest import png_bytes


def post(client, kind, name, data, mime="application/octet-stream"):
    return client.post("/api/v1/uploads", files={"file": (name, data, mime)}, data={"kind": kind})


def test_free_accounts_cannot_upload(client):
    r = post(client, "avatar", "a.png", png_bytes())
    assert r.status_code == 403 and "Lifetime" in r.json()["detail"]


def test_lifetime_avatar_round_trip(client, world):
    world.plan = "lifetime"
    r = post(client, "avatar", "a.png", png_bytes())
    assert r.status_code == 201
    url = r.json()["url"]
    assert url.startswith("/u/") and url.endswith(".png")
    assert client.get(url).status_code == 200
    listing = client.get("/api/v1/uploads").json()
    assert listing["files"][0]["url"] == url
    name = listing["files"][0]["name"]
    assert client.delete(f"/api/v1/uploads/{name}").status_code == 200
    assert client.get(url).status_code == 404


def test_type_is_sniffed_not_trusted(client, world):
    world.plan = "lifetime"
    assert post(client, "avatar", "a.png", b"MZ\x90\x00" + b"x" * 100, "image/png").status_code == 400
    assert post(client, "audio", "s.mp3", b"ID3\x04\x00" + b"\x00" * 200).status_code == 201
    assert post(client, "video", "v.mp4", b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 100).status_code == 201


def test_cursor_needs_supporter_and_stays_small(client, world):
    world.plan = "lifetime"
    assert post(client, "cursor", "c.png", png_bytes()).status_code == 403
    world.plan = "supporter"
    assert post(client, "cursor", "c.png", png_bytes((300, 300))).status_code == 400
    assert post(client, "cursor", "c.png", png_bytes()).status_code == 201


def test_bad_kind_and_traversal(client, world):
    world.plan = "supporter"
    assert post(client, "nope", "a.png", png_bytes()).status_code == 400
    assert client.delete("/api/v1/uploads/../../etc/passwd").status_code == 404
    assert client.get("/u/../app/main.py").status_code == 404
