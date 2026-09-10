from datetime import datetime
from typing import Annotated
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.core.sessions import get_user_from_request
from app.db import admin_db, data_api
from app.models import User

router = APIRouter(prefix="/admin", tags=["admin"])
SettingsDep = Annotated[Settings, Depends(get_settings)]


async def require_admin(request: Request, settings: SettingsDep) -> User:
    user = await get_user_from_request(request)
    if user is None or (not user.is_admin and user.id not in settings.admin_user_id_list):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access is required.")
    return user


AdminUser = Annotated[User, Depends(require_admin)]


class SuspensionRequest(BaseModel):
    suspended: bool
    reason: str | None = Field(default=None, max_length=500)
    until: datetime | None = None


class ReservedUsernameRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    reason: str | None = Field(default=None, max_length=500)


class BadgeRequest(BaseModel):
    id: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9-]+$")
    name: str = Field(min_length=1, max_length=128)
    description: str = Field(default="", max_length=500)
    color: str = Field(default="#9b87f5", max_length=32)


class UserBadgeRequest(BaseModel):
    enabled: bool = True


class EntitlementRequest(BaseModel):
    user_id: UUID
    plan: str = Field(min_length=1, max_length=64)
    active: bool = True
    expires_at: datetime | None = None


class ReportRequest(BaseModel):
    status: str = Field(pattern=r"^(open|reviewed|resolved|dismissed)$")


class FeatureFlagRequest(BaseModel):
    enabled: bool
    description: str = Field(default="", max_length=500)


class ThemeRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    config: dict = Field(default_factory=dict)
    active: bool = True


@router.get("/users")
async def users(
    _admin: AdminUser,
    search: str = Query(default="", max_length=128),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict:
    return {"users": await admin_db.search_users(search, limit, offset), "limit": limit, "offset": offset}


@router.patch("/users/{user_id}/suspension")
async def suspension(user_id: UUID, payload: SuspensionRequest, admin: AdminUser) -> dict:
    changed = await admin_db.set_suspension(admin.id, user_id, payload.suspended, payload.reason, payload.until)
    if not changed:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"ok": True}


@router.get("/reserved-usernames")
async def reserved_usernames(_admin: AdminUser) -> dict:
    return {"reserved": await admin_db.list_reserved()}


@router.post("/reserved-usernames", status_code=201)
async def add_reserved_username(payload: ReservedUsernameRequest, admin: AdminUser) -> dict:
    try:
        await admin_db.add_reserved(admin.id, payload.username.strip().lower(), payload.reason)
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=409, detail="That username is already reserved.") from None
    return {"ok": True}


@router.delete("/reserved-usernames/{username}")
async def remove_reserved_username(username: str, admin: AdminUser) -> dict:
    if not await admin_db.remove_reserved(admin.id, username):
        raise HTTPException(status_code=404, detail="Reserved username not found.")
    return {"ok": True}


@router.get("/badges")
async def badges(_admin: AdminUser) -> dict:
    return {"badges": await admin_db.list_badges()}


@router.post("/badges", status_code=201)
async def add_badge(payload: BadgeRequest, admin: AdminUser) -> dict:
    try:
        await admin_db.add_badge(admin.id, payload.id, payload.name, payload.description, payload.color)
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=409, detail="That badge ID already exists.") from None
    return {"ok": True}


@router.put("/users/{user_id}/badges/{badge_id}")
async def assign_badge(user_id: UUID, badge_id: str, payload: UserBadgeRequest, admin: AdminUser) -> dict:
    try:
        await admin_db.assign_badge(admin.id, user_id, badge_id, payload.enabled)
    except asyncpg.ForeignKeyViolationError:
        raise HTTPException(status_code=404, detail="User or badge not found.") from None
    return {"ok": True}


@router.get("/entitlements")
async def entitlements(_admin: AdminUser) -> dict:
    return {"entitlements": await admin_db.list_entitlements()}


@router.post("/entitlements", status_code=201)
async def add_entitlement(payload: EntitlementRequest, admin: AdminUser) -> dict:
    try:
        entitlement_id = await admin_db.add_entitlement(admin.id, payload.user_id, payload.plan, payload.active, payload.expires_at)
    except asyncpg.ForeignKeyViolationError:
        raise HTTPException(status_code=404, detail="User not found.") from None
    return {"id": entitlement_id}


@router.get("/reports")
async def reports(_admin: AdminUser) -> dict:
    return {"reports": await admin_db.list_reports()}


@router.patch("/reports/{report_id}")
async def update_report(report_id: UUID, payload: ReportRequest, admin: AdminUser) -> dict:
    if not await admin_db.update_report(admin.id, report_id, payload.status):
        raise HTTPException(status_code=404, detail="Report not found.")
    return {"ok": True}


@router.get("/feature-flags")
async def feature_flags(_admin: AdminUser) -> dict:
    return {"flags": await admin_db.list_flags()}


@router.put("/feature-flags/{key}")
async def update_feature_flag(key: str, payload: FeatureFlagRequest, admin: AdminUser) -> dict:
    await admin_db.update_flag(admin.id, key, payload.enabled, payload.description)
    return {"ok": True}


@router.get("/audit-logs")
async def audit_logs(_admin: AdminUser) -> dict:
    return {"logs": await admin_db.list_audit_logs()}


@router.get("/bakaboost")
async def bakaboost(_admin: AdminUser) -> dict:
    return {"connections": await admin_db.list_bakaboost_connections()}


@router.get("/themes")
async def themes(_admin: AdminUser) -> dict:
    return {"themes": await admin_db.list_themes()}


@router.post("/themes", status_code=201)
async def save_theme(payload: ThemeRequest, admin: AdminUser) -> dict:
    try:
        theme_id = await admin_db.save_theme(admin.id, payload.name, payload.config, payload.active)
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=409, detail="That theme name already exists.") from None
    return {"id": theme_id}


@router.delete("/users/{user_id}")
async def delete_user(user_id: UUID, admin: AdminUser, settings: SettingsDep) -> dict:
    """Delete an account outright (spam, impersonation). Suspension is reversible; this is not — the name goes back in the pool."""
    from app.api.v1.users import cleanup_after_delete

    if str(user_id) == str(admin.id):
        raise HTTPException(status_code=400, detail="Delete your own account from the dashboard, not here.")
    try:
        target = await data_api.get_user(str(user_id))
        deleted = await data_api.delete_user(str(user_id)) if target else False
    except Exception:
        raise HTTPException(status_code=502, detail="The data API did not answer. Nothing was removed.") from None
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found.")
    await cleanup_after_delete(str(user_id), target.username, settings)
    try:
        async with admin_db._get_pool().acquire() as conn:
            await admin_db._audit(conn, admin.id, "user.delete", "user", str(user_id), {"username": target.username})
    except (RuntimeError, OSError):
        pass
    return {"ok": True, "deleted": str(user_id)}
