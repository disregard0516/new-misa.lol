from contextlib import asynccontextmanager
from html import escape
from pathlib import Path
import json
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException as StarletteHTTPException
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.middleware import RequestContextMiddleware
from app.core.security import USERNAME_RE
from app.core.sessions import get_user_from_request, session_user_id
from app.db import close_admin_db, close_data_api, close_dragonfly, data_api, init_admin_db, init_data_api, init_dragonfly
from app.profile_page import render_public_profile
from app.share_card import cached_card
from app.core.analytics import record_view, total_views
from app.core.rate_limit import client_ip, rate_limit

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
PAGES_DIR = TEMPLATES_DIR / "pages"
PRIVATE_PAGES = {"dashboard", "admin"}
GUEST_PAGES = {"login", "signup"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging("DEBUG" if settings.debug else "INFO")
    init_dragonfly(settings.dragonfly_url)
    try:
        await init_data_api(settings.data_api_url, settings.data_api_key)
    except Exception:
        if not os.environ.get("VERCEL"):
            raise
    await init_admin_db(settings.database_url)
    app.state.settings = settings
    yield
    await close_data_api()
    await close_admin_db()
    await close_dragonfly()


def page_file(name: str) -> Path:
    pages = PAGES_DIR.resolve()
    slug = name.removesuffix(".html") or "index"
    if slug != Path(slug).name or slug in {".", ".."}:
        raise HTTPException(status_code=404)
    path = (pages / slug / "index.html").resolve()
    if not path.is_relative_to(pages) or not path.is_file():
        raise HTTPException(status_code=404)
    return path


def html_response(name: str, status_code: int = 200) -> FileResponse:
    return FileResponse(page_file(name), status_code=status_code, media_type="text/html")


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    application.add_middleware(RequestContextMiddleware)
    application.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router, prefix=settings.api_v1_prefix)

    def frontend_config_js() -> Response:
        current = get_settings()
        preview = os.environ.get("MISA_UI_PREVIEW", "").lower() in {"1", "true", "yes"}
        payload = json.dumps({"turnstileSiteKey": current.turnstile_site_key})
        body = (
            f"window.MISA_CONFIG = {payload};"
            "window.MISA_TURNSTILE_SITE_KEY = window.MISA_CONFIG.turnstileSiteKey;"
            f"window.MISA_UI_PREVIEW = {json.dumps(preview)};"
        )
        return Response(
            body,
            media_type="application/javascript",
            headers={"Cache-Control": "no-store"},
        )

    # Register before the /js StaticFiles mount so this is not shadowed.
    application.add_api_route("/js/config.js", frontend_config_js, methods=["GET"])
    application.add_api_route("/config.js", frontend_config_js, methods=["GET"])

    application.mount("/css", StaticFiles(directory=TEMPLATES_DIR / "css"), name="css")
    application.mount("/js", StaticFiles(directory=TEMPLATES_DIR / "js"), name="js")
    application.mount("/icons", StaticFiles(directory=TEMPLATES_DIR / "icons"), name="icons")
    application.mount("/images", StaticFiles(directory=TEMPLATES_DIR / "images"), name="images")
    uploads_dir = Path(get_settings().upload_dir)
    try:
        uploads_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    if uploads_dir.is_dir():
        # user files: /u/<user_id>/<kind>-<hash>.<ext> — see api/v1/uploads.py
        application.mount("/u", StaticFiles(directory=uploads_dir), name="uploads")

    @application.middleware("http")
    async def static_cache_headers(request: Request, call_next):
        """Versioned static assets (?v=…) and content-hashed uploads (/u/…) can be cached forever; other static files revalidate."""
        response = await call_next(request)
        path = request.url.path
        if path.startswith(("/css/", "/js/", "/images/", "/icons/", "/u/")) and response.status_code == 200:
            if "v" in request.query_params or path.startswith("/u/"):
                response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            elif "Cache-Control" not in response.headers:
                response.headers["Cache-Control"] = "public, no-cache"
        return response

    @application.get("/")
    async def home() -> FileResponse:
        return html_response("index.html")

    @application.get("/robots.txt")
    async def robots() -> FileResponse:
        return FileResponse(TEMPLATES_DIR / "robots.txt", media_type="text/plain")

    @application.get("/site.webmanifest")
    async def manifest() -> FileResponse:
        # v3.91: the web app manifest (name + raster icons for home screens); written by the site build next to robots.txt
        return FileResponse(TEMPLATES_DIR / "site.webmanifest", media_type="application/manifest+json", headers={"Cache-Control": "public, max-age=86400"})

    @application.get("/sitemap.xml")
    async def sitemap() -> Response:
        # the public site pages only; profile pages are not listed (that would be a full user scan on every crawl)
        base = "https://misa.lol"
        urls = "".join(f"<url><loc>{base}{path}</loc></url>" for path in ("/", "/pricing", "/explore", "/signup", "/login", "/terms", "/privacy"))
        body = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
        return Response(content=body, media_type="application/xml", headers={"Cache-Control": "public, max-age=3600"})

    @application.get("/{username}/card.png")
    async def profile_card(username: str, request: Request) -> Response:
        """The share card for misa.lol/<username> — what the link looks like on Discord, X, iMessage."""
        slug = username.lower()
        if not USERNAME_RE.match(slug):
            raise HTTPException(status_code=404)
        await rate_limit(f"rl:card:{client_ip(request)}", 60, 60)
        try:
            user = await data_api.find_user(username=slug)
            profile = await data_api.get_profile(user.id) if user and not user.currently_suspended else None
        except Exception:
            profile = None
        if not profile:
            raise HTTPException(status_code=404)
        png = await run_in_threadpool(cached_card, slug, profile)
        return Response(content=png, media_type="image/png", headers={"Cache-Control": "public, max-age=300"})

    def _preview_on() -> bool:
        return os.environ.get("MISA_UI_PREVIEW", "").lower() in {"1", "true", "yes"}

    @application.get("/preview/qr.png")
    async def preview_qr(request: Request) -> Response:
        if not _preview_on():
            raise HTTPException(status_code=404)
        from app.core.qr import page_qr_png

        base = get_settings().public_base_url.rstrip("/")
        dark = request.query_params.get("theme") == "dark"
        png = await run_in_threadpool(lambda: page_qr_png(f"{base}/you", dark=dark))
        return Response(content=png, media_type="image/png", headers={"Cache-Control": "no-store"})

    @application.get("/ui")
    async def ui_preview() -> FileResponse:
        if not _preview_on():
            raise HTTPException(status_code=404)
        return html_response("dashboard.html")

    @application.get("/{username}/qr.png")
    async def profile_qr(username: str, request: Request) -> Response:
        """QR PNG for the public page."""
        slug = username.lower()
        if not USERNAME_RE.match(slug):
            raise HTTPException(status_code=404)
        await rate_limit(f"rl:qr:{client_ip(request)}", 60, 60)
        try:
            user = await data_api.find_user(username=slug)
            if user is None or user.currently_suspended:
                raise HTTPException(status_code=404)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=404)
        from app.core.qr import page_qr_png

        base = get_settings().public_base_url.rstrip("/")
        dark = request.query_params.get("theme") == "dark"
        try:
            png = await run_in_threadpool(lambda: page_qr_png(f"{base}/{user.username}", dark=dark))
        except ImportError:
            raise HTTPException(status_code=503, detail="QR support is not installed.")
        return Response(content=png, media_type="image/png", headers={"Cache-Control": "public, max-age=86400"})

    @application.get("/{username}/milestone.png")
    async def milestone_card(username: str, request: Request, n: int = 0) -> Response:
        """v3.124: a card for a view count the page has really crossed — 404 for one it hasn't."""
        from app.core.analytics import total_views as _total_views
        from app.milestone_card import MILESTONES, cached_milestone

        slug = username.lower()
        if not USERNAME_RE.match(slug) or n not in MILESTONES:
            raise HTTPException(status_code=404)
        await rate_limit(f"rl:card:{client_ip(request)}", 60, 60)
        try:
            user = await data_api.find_user(username=slug)
            profile = await data_api.get_profile(user.id) if user and not user.currently_suspended else None
            views = await _total_views(user.id) if profile else 0
        except Exception:
            profile, views = None, 0
        if not profile or views < n:
            raise HTTPException(status_code=404)
        png = await run_in_threadpool(cached_milestone, slug, profile, n)
        return Response(content=png, media_type="image/png", headers={"Cache-Control": "public, max-age=300"})

    @application.get("/{page}", response_model=None)
    async def html_page(page: str, request: Request) -> FileResponse | RedirectResponse:
        slug = page.removesuffix(".html") or "index"
        if slug in PRIVATE_PAGES | GUEST_PAGES:
            user = await get_user_from_request(request)
            if slug == "admin":
                if user is None or not (user.is_admin or user.id in get_settings().admin_user_id_list):
                    raise HTTPException(status_code=404)
            elif slug in PRIVATE_PAGES and user is None:
                preview = os.environ.get("MISA_UI_PREVIEW", "").lower() in {"1", "true", "yes"}
                if not (preview and slug == "dashboard"):
                    return RedirectResponse("/login", status_code=302)
            if slug in GUEST_PAGES and user is not None:
                return RedirectResponse("/dashboard", status_code=302)
        # site pages first: their slugs are reserved usernames, so no need to hit the data API for /pricing etc.
        try:
            return html_response(f"{slug}.html")
        except HTTPException:
            pass
        try:
            user = await data_api.find_user(username=slug.lower())
            if user and not user.currently_suspended:   # a suspended account's page is simply gone
                profile = await data_api.get_profile(user.id)
                if profile:
                    views = None
                    try:
                        settings = get_settings()
                        await record_view(user.id, request, salt=settings.analytics_salt or settings.data_api_key or "misa", own_domain=settings.domain, viewer_id=await session_user_id(request))
                        views = await total_views(user.id)
                    except Exception:
                        pass  # analytics never break a page
                    if (profile.get("settings") or {}).get("replay"):  # v3.127: the visitor's-eye replay — one line per arrival, only for the owner
                        try:
                            from app.core.analytics import BOT_RE as _BOT, visitor_hash as _vh
                            from app.core.replay import note as replay_note, phone_like
                            ua = request.headers.get("user-agent", "")
                            if not _BOT.search(ua):
                                rs = get_settings()
                                from urllib.parse import urlsplit
                                ref = (urlsplit(request.headers.get("referer", "")).hostname or "").lower()
                                if ref == rs.domain or ref.endswith("." + rs.domain):
                                    ref = ""
                                await replay_note(user.id, "in", _vh(request, rs.analytics_salt or rs.data_api_key or "misa")[:8], ref, phone=phone_like(ua))
                        except Exception:
                            pass
                    here = None
                    if (profile.get("settings") or {}).get("presence"):  # v3.118: this visitor is here, so count them now
                        try:
                            from app.core.analytics import BOT_RE, visitor_hash
                            from app.core.presence import beat as presence_beat, here as presence_here
                            s = get_settings()
                            salt = s.analytics_salt or s.data_api_key or "misa"
                            here = await (presence_here(user.id) if BOT_RE.search(request.headers.get("user-agent", "")) else presence_beat(user.id, visitor_hash(request, salt)))
                        except Exception:
                            here = None
                    # v3.143: ?as=<second> — this page as it was, when its owner lets its past be read
                    was_at = None
                    try:
                        raw_as = request.query_params.get("as")
                        if raw_as and (profile.get("settings") or {}).get("archive"):
                            from app.core.archive import at as archive_at
                            older = await archive_at(user.id, int(raw_as))
                            if older:
                                was_at, profile = int(raw_as), older
                    except (TypeError, ValueError):
                        was_at = None
                    except Exception:
                        was_at = None
                    parts = {}
                    try:  # v3.137: the guestbook, chalkboard, ask box, vigil, sky and block feeds — the same gathering the dashboard's preview uses
                        from app.core.analytics import visitor_hash as _pvh
                        from app.core.page_parts import gather as gather_parts
                        ps = get_settings()
                        parts = await gather_parts(user.id, profile, _pvh(request, ps.analytics_salt or ps.data_api_key or "misa")[:8])
                    except Exception:
                        parts = {}
                    return HTMLResponse(render_public_profile(profile, views=views, here=here, since=getattr(user, "created_at", None), was_at=was_at, **parts), headers={"Cache-Control": "no-store"})
        except Exception:
            pass
        preview = os.environ.get("MISA_UI_PREVIEW", "").lower() in {"1", "true", "yes"}
        if preview and slug.lower() == "you":
            return HTMLResponse(
                render_public_profile(
                    {
                        "profile": {
                            "username": "you",
                            "displayName": "you",
                            "description": "be weird online again.",
                            "location": "the void",
                            "pronouns": "they/them",
                        },
                        "settings": {
                            "accentColor": "#F00646",
                            "textColor": "#F2F2F0",
                            "backgroundColor": "#050606",
                            "backgroundColor2": "#1a0a10",
                            "showViews": True,
                            "showSocials": True,
                            "backgroundEffect": "Glow",
                            "usernameEffect": "Shimmer",
                            "layout": "modern",
                        },
                        "assets": {},
                        "socials": [
                            {"id": "s1", "platform": "X", "label": "x", "value": "https://x.com", "enabled": True},
                            {"id": "s2", "platform": "Discord", "label": "discord", "value": "https://discord.gg", "enabled": True},
                            {"id": "s3", "platform": "GitHub", "label": "github", "value": "https://github.com", "enabled": True},
                            {"id": "s4", "platform": "Spotify", "label": "spotify", "value": "https://open.spotify.com", "enabled": True},
                        ],
                        "badges": [{"name": "early", "color": "#F00646", "owned": True, "enabled": True}],
                    },
                    views=12840,
                ),
                headers={"Cache-Control": "no-store"},
            )
        raise HTTPException(status_code=404)

    @application.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> HTMLResponse | JSONResponse:
        if request.url.path.startswith("/api"):
            return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
        if exc.status_code >= 500:
            return HTMLResponse(
                "<!DOCTYPE html><title>Server error</title><h1>Server error</h1>",
                status_code=exc.status_code,
            )
        not_found = PAGES_DIR / "404" / "index.html"
        if not_found.is_file():
            return HTMLResponse(not_found.read_text(encoding="utf-8"), status_code=404)
        return HTMLResponse(
            "<!DOCTYPE html><title>Not found</title><h1>Page not found</h1><p><a href='/'>Back home</a></p>",
            status_code=404,
        )

    return application


app = create_app()
