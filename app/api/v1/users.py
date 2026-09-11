from typing import Annotated

import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.analytics import forget_user, record_click, stats as analytics_stats
from app.core.rate_limit import client_ip, rate_limit
from app.core.security import USERNAME_RE, hash_password, validate_username, verify_password
from app.core.sessions import clear_session_cookie, destroy_session
from app.share_card import forget_card
from app.core.config import Settings, get_settings
from app.core.sessions import get_user_from_request
from app.db import admin_db, data_api
from app.db.dragonfly import get_dragonfly
from app.db.data_api import DataConflict
from app.models import User

router = APIRouter(tags=["users"])
SettingsDep = Annotated[Settings, Depends(get_settings)]


def public_user(user: User, settings: Settings) -> dict:
    payload = user.to_public_dict()
    payload["is_admin"] = user.is_admin or user.id in settings.admin_user_id_list
    return payload


class UsernameRequest(BaseModel):
    username: str = Field(min_length=3, max_length=24)


class DisplayNameRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=128)


async def require_user(request: Request) -> User:
    user = await get_user_from_request(request)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    return user


async def plan_and_badges(user_id) -> tuple[str, dict | None, list[dict]]:
    """Plan + owned badges from the admin tables; degrades to free / none if that database is down."""
    try:
        ent = await admin_db.user_plan(user_id)
        badges = await admin_db.user_badges(user_id)
    except (RuntimeError, OSError):
        return "free", None, []
    return (ent["plan"] if ent else "free"), ent, badges


@router.get("/me")
async def me(user: Annotated[User, Depends(require_user)], settings: SettingsDep) -> dict:
    payload = public_user(user, settings)
    plan, ent, badges = await plan_and_badges(user.id)
    payload["plan"] = plan
    payload["plan_expires_at"] = ent["expires_at"] if ent else None
    payload["badges"] = badges
    return payload


class BadgeToggleRequest(BaseModel):
    enabled: bool


@router.patch("/me/badges/{badge_id}")
async def toggle_badge(badge_id: str, payload: BadgeToggleRequest, user: Annotated[User, Depends(require_user)]) -> dict:
    try:
        ok = await admin_db.set_badge_enabled(user.id, badge_id[:64], payload.enabled)
    except (RuntimeError, OSError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Badges are unavailable right now.") from None
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You don't have that badge.")
    return {"badges": await admin_db.user_badges(user.id)}


@router.patch("/me/username")
async def set_username(
    payload: UsernameRequest,
    user: Annotated[User, Depends(require_user)],
    settings: SettingsDep,
) -> dict:
    try:
        username = validate_username(payload.username)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from None
    if await admin_db.is_reserved(username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="That username is reserved.")
    try:
        updated = await data_api.update_user(user.id, username=username)
    except DataConflict:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="That username is taken.") from None
    if updated is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    # v3.36: the public page and the share card read the name from the saved profile config, so a rename
    # has to follow into it — otherwise misa.lol/<new> kept showing "misa.lol/<old>" until the next dashboard save.
    old_name = (user.username or "").lower()
    try:
        profile = await data_api.get_profile(user.id)
        if profile and isinstance(profile.get("profile"), dict) and profile["profile"].get("username") != username:
            profile["profile"]["username"] = username
            await data_api.save_profile(user.id, profile)
    except Exception:
        pass  # the rename itself succeeded; the next save syncs the config
    if old_name:
        forget_card(old_name)
    forget_card(username)
    try:
        await get_dragonfly().delete("explore:listed")
    except Exception:
        pass
    return public_user(updated, settings)


@router.patch("/me")
async def update_me(
    payload: DisplayNameRequest,
    user: Annotated[User, Depends(require_user)],
    settings: SettingsDep,
) -> dict:
    updated = await data_api.update_user(user.id, display_name=payload.display_name.strip())
    if updated is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    return public_user(updated, settings)


@router.get("/me/stats")
async def my_stats(user: Annotated[User, Depends(require_user)]) -> dict:
    """Views (total / today / 7 days / 14 daily buckets), top referrers, link clicks, countries — counted server-side."""
    try:
        data = await analytics_stats(user.id)
    except (RuntimeError, OSError):
        return {"views": 0, "today": 0, "week": 0, "daily": [], "referrers": [], "clicks": [], "countries": [], "unavailable": True}
    # label the clicks with the current links
    labels: dict[str, str] = {}
    try:
        profile = await data_api.get_profile(user.id) or {}
        for s in profile.get("socials") or []:
            if isinstance(s, dict) and s.get("id"):
                labels[str(s["id"])] = str(s.get("label") or s.get("platform") or s["id"])
    except Exception:
        pass
    data["clicks"] = [[sid, labels.get(sid, sid), n] for sid, n in data["clicks"]]
    return data


@router.post("/hit/{username}/{social_id}", status_code=204)
async def hit(username: str, social_id: str, request: Request) -> Response:
    """Click beacon from a public page (navigator.sendBeacon). Public, tiny, and it never says whether the name exists."""
    slug = username.lower()
    if USERNAME_RE.match(slug) and len(social_id) <= 64:
        try:
            await rate_limit(f"rl:hit:{client_ip(request)}", 120, 60)
            user = await data_api.find_user(username=slug)
            if user:
                await record_click(user.id, social_id)
                try:  # v3.127: and into the replay, when the owner keeps one
                    profile = await data_api.get_profile(user.id) or {}
                    if (profile.get("settings") or {}).get("replay"):
                        from app.core.analytics import BOT_RE, visitor_hash
                        from app.core.replay import note as replay_note, phone_like
                        ua = request.headers.get("user-agent", "")
                        if not BOT_RE.search(ua):
                            s = get_settings()
                            await replay_note(user.id, "tap", visitor_hash(request, s.analytics_salt or s.data_api_key or "misa")[:8], social_id, phone=phone_like(ua))
                except Exception:
                    pass
        except Exception:
            pass
    return Response(status_code=204)


async def cleanup_after_delete(user_id: str, username: str | None, settings: Settings) -> None:
    """After an account is gone: its uploads folder, analytics keys and cached card (best effort — an orphaned file is no reason to fail)."""
    base = Path(settings.upload_dir).resolve()
    mine = (base / user_id).resolve()
    if mine.is_relative_to(base) and mine != base and mine.is_dir():
        shutil.rmtree(mine, ignore_errors=True)
    try:
        await forget_user(user_id)
        try:
            from app.core.guestbook import forget as forget_book
            await forget_book(user_id)
        except Exception:
            pass
        try:
            from app.core.presence import forget as forget_presence
            await forget_presence(user_id)
        except Exception:
            pass
        try:
            from app.core.doodles import forget as forget_doodles
            await forget_doodles(user_id)
        except Exception:
            pass
        try:
            from app.core.replay import forget as forget_replay
            await forget_replay(user_id)
        except Exception:
            pass
        try:
            from app.core.asks import forget as forget_asks
            await forget_asks(user_id)
        except Exception:
            pass
        try:
            from app.core.vigil import forget as forget_vigil
            await forget_vigil(user_id)
        except Exception:
            pass
        try:
            from app.core.tally import forget as forget_tally
            await forget_tally(user_id)
        except Exception:
            pass
        try:
            from app.core.archive import forget as forget_archive
            await forget_archive(user_id)
        except Exception:
            pass
        try:
            from app.core.neighbours import forget as forget_neighbours
            await forget_neighbours(user_id)
        except Exception:
            pass
    except (RuntimeError, OSError):
        pass
    if username:
        forget_card(username.lower())
    try:
        from app.db.dragonfly import get_dragonfly

        await get_dragonfly().delete("explore:listed")
    except (RuntimeError, OSError):
        pass


class DeleteAccountRequest(BaseModel):
    confirm: str = Field(min_length=1, max_length=32)
    password: str | None = Field(default=None, max_length=256)


@router.delete("/me")
async def delete_me(payload: DeleteAccountRequest, request: Request, user: Annotated[User, Depends(require_user)], settings: SettingsDep) -> JSONResponse:
    """Delete the account: uploads, analytics, the cached card, then the user itself (profile, badges, grants cascade). Signs out."""
    if payload.confirm.strip().lower() != "delete":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Type delete to confirm.")
    if user.password_hash and not (payload.password and verify_password(user.password_hash, payload.password)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Wrong password.")
    try:
        deleted = await data_api.delete_user(user.id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Could not delete the account right now. Nothing was removed.") from None
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")
    await cleanup_after_delete(user.id, user.username, settings)
    await destroy_session(request.cookies.get(settings.session_cookie_name))
    response = JSONResponse({"ok": True, "redirect": "/"})
    clear_session_cookie(response, request, settings)
    return response


class PasswordRequest(BaseModel):
    current_password: str | None = Field(default=None, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


@router.patch("/me/password")
async def set_password(payload: PasswordRequest, request: Request, user: Annotated[User, Depends(require_user)], settings: SettingsDep) -> dict:
    """Change the password, or set one on an account that signed up with Google / Discord / Telegram."""
    await rate_limit(f"rl:password:{user.id}", 10, 3600)
    if user.password_hash and not (payload.current_password and verify_password(user.password_hash, payload.current_password)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Current password is wrong.")
    if payload.current_password and payload.current_password == payload.new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="That's the same password.")
    updated = await data_api.update_user(user.id, password_hash=hash_password(payload.new_password))
    if updated is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    return public_user(updated, settings)
