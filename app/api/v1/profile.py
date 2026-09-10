import copy
from typing import Any, Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from httpx import HTTPError

from app.core.analytics import total_views
from app.core.plans import gate_profile
from app.core.rate_limit import rate_limit
from app.profile_page import render_public_profile
from app.share_card import forget_card
from app.core.sessions import get_user_from_request
from app.db import admin_db, data_api
from app.db.dragonfly import get_dragonfly
from app.models import User

router = APIRouter(prefix="/profile", tags=["profiles"])


async def require_user(request: Request) -> User:
    user = await get_user_from_request(request)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    return user


@router.get("")
async def public_profile(username: Annotated[str, Query(min_length=3, max_length=24)]) -> dict[str, Any]:
    user = await data_api.find_user(username=username.strip().lower())
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
    profile = await data_api.get_profile(user.id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
    return {"profile": profile}


@router.get("/me")
async def my_profile(user: User = Depends(require_user)) -> dict[str, Any]:
    profile = await data_api.get_profile(user.id)
    if profile is None:
        return {"profile": None}
    return {"profile": profile}


@router.put("/me")
async def save_my_profile(payload: dict[str, Any], user: User = Depends(require_user)) -> dict[str, Any]:
    if not isinstance(payload, dict) or not isinstance(payload.get("profile"), dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid profile payload.")
    if not user.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Choose a username before saving your profile.")
    profile = payload["profile"]
    if str(profile.get("username", "")).strip().lower() != user.username.lower():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profile username does not match the signed-in account.")
    profile["username"] = user.username
    profile["uid"] = user.id
    profile["views"] = await total_views(user.id)  # counted on the server; whatever the client sent is ignored
    display_name = str(profile.get("displayName", "")).strip()
    if not display_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Display name cannot be empty.")
    # badges are granted, never self-declared: rebuild the list from user_badges, keeping only the show/hide choice
    # for badges the user owns; paid-only cosmetics the plan doesn't cover are cleared (see app/core/plans.py)
    # (the request body is the whole ProfileConfig: profile / settings / assets / socials / badges)
    cleared: list[str] = []
    try:
        owned = await admin_db.user_badges(user.id)
        ent = await admin_db.user_plan(user.id)
    except (RuntimeError, OSError):
        # admin database down: keep whatever badges were stored before and skip gating rather than strip a paying user
        try:
            previous = await data_api.get_profile(user.id) or {}
        except (HTTPError, RuntimeError, ValueError):
            previous = {}
        payload["badges"] = previous.get("badges") or []
    else:
        wanted = {str(b.get("id") or b.get("name")): bool(b.get("enabled", True)) for b in (payload.get("badges") or []) if isinstance(b, dict)}
        payload["badges"] = [
            {"id": b["id"], "name": b["name"], "description": b["description"], "color": b["color"], "owned": True,
             "enabled": wanted.get(b["id"], wanted.get(b["name"], bool(b["enabled"])))}
            for b in owned
        ]
        cleared = gate_profile(payload, ent["plan"] if ent else "free")
    previous_page = None
    try:  # v3.143: the archive — shelve the page this save is about to replace
        previous_page = await data_api.get_profile(user.id)
    except Exception:
        previous_page = None
    try:
        updated = await data_api.update_user(user.id, display_name=display_name)
        if updated is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
        saved = await data_api.save_profile(user.id, payload)
    except HTTPException:
        raise
    except (HTTPError, RuntimeError, ValueError):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Profile storage is temporarily unavailable. Please try again.") from None
    if previous_page:
        try:
            from app.core.archive import keep as archive_keep
            await archive_keep(user.id, previous_page)
        except Exception:
            pass
    forget_card(user.username.lower())
    try:
        await get_dragonfly().delete("explore:listed")
    except (RuntimeError, OSError):
        pass
    return {"profile": saved, "cleared": cleared}


@router.post("/me/preview")
async def preview_my_profile(payload: dict[str, Any], request: Request, user: User = Depends(require_user)) -> dict[str, Any]:
    """v3.137: the page this config would make, rendered by the very same code the live page uses.

    Nothing is saved and nothing is counted — no view, no presence, nothing in the replay. The plan is applied
    to a copy first, so what comes back is what would actually go up, and `cleared` names anything the plan
    drops. The guestbook, chalkboard, ask box, vigil and sky are the owner's real ones.
    """
    if not isinstance(payload, dict) or not isinstance(payload.get("profile"), dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid profile payload.")
    await rate_limit(f"rl:pv:{user.id}", 60, 300)
    draft = copy.deepcopy(payload)
    draft["profile"]["username"] = user.username or draft["profile"].get("username") or "you"
    draft["profile"]["uid"] = user.id
    cleared: list[str] = []
    try:
        ent = await admin_db.user_plan(user.id)
        cleared = gate_profile(draft, ent["plan"] if ent else "free")
    except (RuntimeError, OSError):
        cleared = []
    try:
        draft["profile"]["views"] = await total_views(user.id)
    except Exception:
        pass
    try:
        from app.core.page_parts import gather as gather_parts
        parts = await gather_parts(user.id, draft)
    except Exception:
        parts = {}
    html = render_public_profile(draft, views=draft["profile"].get("views"), since=getattr(user, "created_at", None), **parts)
    return {"html": html, "cleared": cleared}


@router.get("/me/archive")
async def my_archive(user: User = Depends(require_user)) -> dict[str, Any]:
    """v3.143: the days this page has been, newest first. Bodies stay here until one is asked for."""
    from app.core.archive import MAX, shelf
    return {"kept": MAX, "days": await shelf(user.id)}


@router.get("/me/archive/{when}")
async def my_archive_one(when: int, user: User = Depends(require_user)) -> dict[str, Any]:
    from app.core.archive import at as archive_at
    cfg = await archive_at(user.id, when)
    if cfg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That one has fallen off the shelf.")
    return {"at": when, "profile": cfg}


@router.post("/me/archive/{when}/restore")
async def restore_my_page(when: int, user: User = Depends(require_user)) -> dict[str, Any]:
    """Put a day back. What is there now is shelved first, so restoring is itself undoable."""
    from app.core.archive import at as archive_at, keep as archive_keep
    cfg = await archive_at(user.id, when)
    if cfg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That one has fallen off the shelf.")
    try:
        now_page = await data_api.get_profile(user.id)
        if now_page:
            await archive_keep(user.id, now_page)
    except Exception:
        pass
    cfg = copy.deepcopy(cfg)
    cfg.setdefault("profile", {})["username"] = user.username or cfg.get("profile", {}).get("username")
    cfg["profile"]["uid"] = user.id
    try:
        cfg["profile"]["views"] = await total_views(user.id)
        ent = await admin_db.user_plan(user.id)
        gate_profile(cfg, ent["plan"] if ent else "free")
    except (RuntimeError, OSError):
        pass
    try:
        saved = await data_api.save_profile(user.id, cfg)
    except (HTTPError, RuntimeError, ValueError):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Profile storage is temporarily unavailable. Please try again.") from None
    if user.username:
        forget_card(user.username.lower())
    try:
        await get_dragonfly().delete("explore:listed")
    except (RuntimeError, OSError):
        pass
    return {"ok": True, "profile": saved}
