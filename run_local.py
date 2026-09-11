"""Local preview without Docker: stub data API + in-memory Redis (fakeredis)."""
from __future__ import annotations

import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UPLOADS = ROOT / "uploads"
UPLOADS.mkdir(exist_ok=True)

os.environ["MISA_ENVIRONMENT"] = "development"
os.environ["MISA_UI_PREVIEW"] = "true"
os.environ["MISA_DEBUG"] = "true"
os.environ["MISA_DOMAIN"] = "localhost"
os.environ["MISA_PUBLIC_BASE_URL"] = "http://127.0.0.1:8000"
os.environ["MISA_CORS_ORIGINS"] = "http://127.0.0.1:8000,http://localhost:8000,http://127.0.0.1:80"
os.environ["MISA_DATA_API_URL"] = "http://127.0.0.1:18080"
os.environ["MISA_DATA_API_KEY"] = "local-dev"
os.environ["MISA_UPLOAD_DIR"] = str(UPLOADS)
os.environ["MISA_DRAGONFLY_URL"] = "redis://127.0.0.1:9/0"
os.environ.pop("DATABASE_URL", None)
os.environ.pop("MISA_DATABASE_URL", None)


class _Stub(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}' if self.path.startswith("/health") else b"null")

    def do_POST(self) -> None:
        self.do_GET()

    def do_PATCH(self) -> None:
        self.do_GET()

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    threading.Thread(
        target=lambda: HTTPServer(("127.0.0.1", 18080), _Stub).serve_forever(),
        daemon=True,
    ).start()

    import fakeredis.aioredis as fakeredis

    fake = fakeredis.FakeRedis(decode_responses=True)

    import app.db.dragonfly as dragonfly
    import app.main as main_mod

    def init_fake(_url: str):
        dragonfly._client = fake
        return fake

    async def close_fake() -> None:
        dragonfly._client = None

    dragonfly.init_dragonfly = init_fake
    dragonfly.close_dragonfly = close_fake
    main_mod.init_dragonfly = init_fake
    main_mod.close_dragonfly = close_fake

    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    print(f"misa.lol local: http://127.0.0.1:{port}/ui")
    uvicorn.run(main_mod.app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    main()
