import json
from typing import Any
from uuid import UUID, uuid4

import asyncpg

_pool: asyncpg.Pool | None = None


async def init_admin_db(database_url: str) -> None:
    global _pool
    if not database_url:
        return
    _pool = await asyncpg.create_pool(database_url, min_size=1, max_size=3, command_timeout=10)


async def close_admin_db() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
    _pool = None


def _get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("admin database is not initialised")
    return _pool


async def _audit(conn: asyncpg.Connection, actor_id: UUID, action: str, target_type: str | None, target_id: str | None, metadata: dict[str, Any] | None = None) -> None:
    await conn.execute(
        "INSERT INTO audit_logs (actor_user_id, action, target_type, target_id, metadata) VALUES ($1,$2,$3,$4,$5::jsonb)",
        actor_id, action, target_type, target_id, json.dumps(metadata or {}),
    )


async def search_users(search: str = "", limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    term = f"%{search.strip()}%"
    rows = await _get_pool().fetch(
        """SELECT id, email, email_verified, username, display_name, avatar_url,
                  google_id, discord_id, telegram_id, telegram_username,
                  created_at, updated_at, last_login_at, is_admin,
                  suspended_at, suspension_reason, suspended_until
           FROM users
           WHERE $1 = '%' OR id::text ILIKE $1 OR COALESCE(username, '') ILIKE $1 OR COALESCE(email, '') ILIKE $1
           ORDER BY created_at DESC LIMIT $2 OFFSET $3""",
        term, max(1, min(limit, 100)), max(0, offset),
    )
    return [dict(row) for row in rows]


async def set_suspension(actor_id: UUID, user_id: UUID, suspended: bool, reason: str | None, until: Any) -> bool:
    async with _get_pool().acquire() as conn:
        async with conn.transaction():
            result = await conn.execute(
                "UPDATE users SET suspended_at = CASE WHEN $2 THEN NOW() ELSE NULL END, suspension_reason = CASE WHEN $2 THEN $3 ELSE NULL END, suspended_until = CASE WHEN $2 THEN $4 ELSE NULL END, updated_at = NOW() WHERE id = $1",
                user_id, suspended, reason, until,
            )
            if result != "UPDATE 1":
                return False
            await _audit(conn, actor_id, "user.suspend" if suspended else "user.unsuspend", "user", str(user_id), {"reason": reason, "until": str(until) if until else None})
    return True


async def list_reserved() -> list[dict[str, Any]]:
    return [dict(row) for row in await _get_pool().fetch("SELECT username, reason, created_by, created_at FROM reserved_usernames ORDER BY username")]


async def is_reserved(username: str) -> bool:
    row = await _get_pool().fetchrow("SELECT 1 FROM reserved_usernames WHERE username = $1", username.lower())
    return row is not None


async def add_reserved(actor_id: UUID, username: str, reason: str | None) -> None:
    async with _get_pool().acquire() as conn:
        async with conn.transaction():
            await conn.execute("INSERT INTO reserved_usernames (username, reason, created_by) VALUES ($1,$2,$3)", username.lower(), reason, actor_id)
            await _audit(conn, actor_id, "reserved_username.create", "reserved_username", username.lower(), {"reason": reason})


async def remove_reserved(actor_id: UUID, username: str) -> bool:
    async with _get_pool().acquire() as conn:
        async with conn.transaction():
            result = await conn.execute("DELETE FROM reserved_usernames WHERE username = $1", username.lower())
            if result != "DELETE 1":
                return False
            await _audit(conn, actor_id, "reserved_username.delete", "reserved_username", username.lower())
    return True


async def list_badges() -> list[dict[str, Any]]:
    return [dict(row) for row in await _get_pool().fetch("SELECT id, name, description, color, created_at FROM badges ORDER BY name")]


async def add_badge(actor_id: UUID, badge_id: str, name: str, description: str, color: str) -> None:
    async with _get_pool().acquire() as conn:
        async with conn.transaction():
            await conn.execute("INSERT INTO badges (id, name, description, color) VALUES ($1,$2,$3,$4)", badge_id, name, description, color)
            await _audit(conn, actor_id, "badge.create", "badge", badge_id, {"name": name})


async def assign_badge(actor_id: UUID, user_id: UUID, badge_id: str, enabled: bool) -> None:
    async with _get_pool().acquire() as conn:
        async with conn.transaction():
            await conn.execute("INSERT INTO user_badges (user_id, badge_id, enabled, granted_by) VALUES ($1,$2,$3,$4) ON CONFLICT (user_id,badge_id) DO UPDATE SET enabled = EXCLUDED.enabled", user_id, badge_id, enabled, actor_id)
            await _audit(conn, actor_id, "badge.assign", "user", str(user_id), {"badge_id": badge_id, "enabled": enabled})


async def list_entitlements() -> list[dict[str, Any]]:
    return [dict(row) for row in await _get_pool().fetch("SELECT id, user_id, plan, active, expires_at, granted_by, created_at FROM premium_entitlements ORDER BY created_at DESC")]


async def add_entitlement(actor_id: UUID, user_id: UUID, plan: str, active: bool, expires_at: Any) -> UUID:
    entitlement_id = uuid4()
    async with _get_pool().acquire() as conn:
        async with conn.transaction():
            await conn.execute("INSERT INTO premium_entitlements (id, user_id, plan, active, expires_at, granted_by) VALUES ($1,$2,$3,$4,$5,$6)", entitlement_id, user_id, plan, active, expires_at, actor_id)
            await _audit(conn, actor_id, "premium.grant", "user", str(user_id), {"plan": plan, "expires_at": str(expires_at) if expires_at else None})
    return entitlement_id


async def list_reports() -> list[dict[str, Any]]:
    return [dict(row) for row in await _get_pool().fetch("SELECT id, reporter_user_id, target_user_id, target_username, reason, details, status, reviewed_by, reviewed_at, created_at FROM reports ORDER BY created_at DESC LIMIT 200")]


async def update_report(actor_id: UUID, report_id: UUID, status: str) -> bool:
    async with _get_pool().acquire() as conn:
        async with conn.transaction():
            result = await conn.execute("UPDATE reports SET status = $2, reviewed_by = $3, reviewed_at = NOW() WHERE id = $1", report_id, status, actor_id)
            if result != "UPDATE 1":
                return False
            await _audit(conn, actor_id, "report.update", "report", str(report_id), {"status": status})
    return True


async def list_flags() -> list[dict[str, Any]]:
    return [dict(row) for row in await _get_pool().fetch("SELECT key, enabled, description, updated_by, updated_at FROM feature_flags ORDER BY key")]


async def update_flag(actor_id: UUID, key: str, enabled: bool, description: str) -> None:
    async with _get_pool().acquire() as conn:
        async with conn.transaction():
            await conn.execute("INSERT INTO feature_flags (key, enabled, description, updated_by, updated_at) VALUES ($1,$2,$3,$4,NOW()) ON CONFLICT (key) DO UPDATE SET enabled = EXCLUDED.enabled, description = EXCLUDED.description, updated_by = EXCLUDED.updated_by, updated_at = NOW()", key, enabled, description, actor_id)
            await _audit(conn, actor_id, "feature_flag.update", "feature_flag", key, {"enabled": enabled})


async def list_audit_logs() -> list[dict[str, Any]]:
    return [dict(row) for row in await _get_pool().fetch("SELECT id, actor_user_id, action, target_type, target_id, metadata, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 300")]


async def list_bakaboost_connections() -> list[dict[str, Any]]:
    return [dict(row) for row in await _get_pool().fetch("SELECT user_id, provider, external_id, status, metadata, connected_at, updated_at FROM bakaboost_connections ORDER BY updated_at DESC")]


async def list_themes() -> list[dict[str, Any]]:
    return [dict(row) for row in await _get_pool().fetch("SELECT id, name, config, active, created_by, updated_by, created_at, updated_at FROM theme_presets ORDER BY name")]


async def save_theme(actor_id: UUID, name: str, config: dict[str, Any], active: bool) -> UUID:
    theme_id = uuid4()
    async with _get_pool().acquire() as conn:
        async with conn.transaction():
            await conn.execute("INSERT INTO theme_presets (id, name, config, active, created_by, updated_by) VALUES ($1,$2,$3::jsonb,$4,$5,$5) ON CONFLICT (name) DO UPDATE SET config = EXCLUDED.config, active = EXCLUDED.active, updated_by = EXCLUDED.updated_by, updated_at = NOW()", theme_id, name, json.dumps(config), active, actor_id)
            await _audit(conn, actor_id, "theme_preset.save", "theme_preset", name, {"active": active})
    return theme_id


# ── per-user reads used by the dashboard (v3.5): plan + badges come from the admin tables, never from the profile JSON ──
async def user_plan(user_id: UUID) -> dict[str, Any] | None:
    """The best active, unexpired entitlement for a user, or None (= free)."""
    rows = await _get_pool().fetch(
        "SELECT plan, expires_at FROM premium_entitlements WHERE user_id = $1 AND active AND (expires_at IS NULL OR expires_at > NOW()) ORDER BY created_at DESC",
        user_id,
    )
    best = None
    for row in rows:
        cand = {"plan": str(row["plan"]).strip().lower(), "expires_at": row["expires_at"]}
        if best is None or _plan_rank(cand["plan"]) > _plan_rank(best["plan"]):
            best = cand
    return best


def _plan_rank(plan: str) -> int:
    return {"free": 0, "lifetime": 1, "supporter": 2}.get(plan, 1)


async def user_badges(user_id: UUID) -> list[dict[str, Any]]:
    rows = await _get_pool().fetch(
        "SELECT b.id, b.name, b.description, b.color, ub.enabled FROM user_badges ub JOIN badges b ON b.id = ub.badge_id WHERE ub.user_id = $1 ORDER BY ub.granted_at",
        user_id,
    )
    return [dict(row) for row in rows]


async def set_badge_enabled(user_id: UUID, badge_id: str, enabled: bool) -> bool:
    """A user may show or hide a badge they own; they can never grant one."""
    result = await _get_pool().execute("UPDATE user_badges SET enabled = $3 WHERE user_id = $1 AND badge_id = $2", user_id, badge_id, enabled)
    return result == "UPDATE 1"


async def add_report(reporter_id: Any, target_user_id: Any, target_username: str, reason: str, details: str) -> UUID:
    """A public report of a page (api/v1/reports.py). No audit row: the reporter isn't an actor with an account, necessarily."""
    report_id = uuid4()
    await _get_pool().execute(
        "INSERT INTO reports (id, reporter_user_id, target_user_id, target_username, reason, details) VALUES ($1,$2,$3,$4,$5,$6)",
        report_id, reporter_id, target_user_id, target_username[:32], reason[:128], details,
    )
    return report_id
