"""File uploads for a page (v3.9): avatar, background image, background video, audio, cursor.

Image hosting is a Lifetime / Supporter perk on the pricing table, so the endpoint requires a plan; free pages
keep using URLs. Files land on the shared uploads volume (settings.upload_dir, default /data/uploads) under
<user_id>/<kind>-<sha256[:16]>.<ext> and are served at /u/<user_id>/<file>. Types are sniffed, never trusted from
the client; images are opened with Pillow; a per-user quota keeps "unlimited" from meaning "a Blu-ray".
"""
from __future__ import annotations

import hashlib
import io
import re
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from PIL import Image, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings, get_settings
from app.core.plans import plan_rank
from app.core.rate_limit import rate_limit
from app.core.sessions import get_user_from_request
from app.db import admin_db
from app.models import User

router = APIRouter(prefix="/uploads", tags=["uploads"])
SettingsDep = Annotated[Settings, Depends(get_settings)]

MB = 1024 * 1024
KINDS: dict[str, dict[str, Any]] = {
    # kind: allowed sniffed types → extension, size cap, minimum plan rank
    "avatar":     {"types": {"png": "png", "jpeg": "jpg", "webp": "webp", "gif": "gif"}, "max": 8 * MB, "plan": 1},
    "background": {"types": {"png": "png", "jpeg": "jpg", "webp": "webp", "gif": "gif"}, "max": 8 * MB, "plan": 1},
    "video":      {"types": {"mp4": "mp4", "webm": "webm"}, "max": 32 * MB, "plan": 1},
    "audio":      {"types": {"mp3": "mp3", "ogg": "ogg", "wav": "wav", "m4a": "m4a"}, "max": 12 * MB, "plan": 1},
    "cursor":     {"types": {"png": "png"}, "max": 256 * 1024, "plan": 2, "max_px": 128},
}
QUOTA_BYTES = 200 * MB          # per user, across everything they've uploaded
NAME_RE = re.compile(r"^[a-z]+-[0-9a-f]{16}\.[a-z0-9]{2,4}$")


async def require_user(request: Request) -> User:
    user = await get_user_from_request(request)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    return user


def sniff(head: bytes) -> str | None:
    """Container type from the first bytes. Deliberately small: only what the dashboard can use."""
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
        return "wav"
    if head.startswith(b"GIF87a") or head.startswith(b"GIF89a"):
        return "gif"
    if head[4:8] == b"ftyp":
        brand = head[8:12]
        if brand in (b"M4A ", b"M4B ", b"mp42") and b"M4A" in head[:32]:
            return "m4a"
        return "mp4"
    if head.startswith(b"\x1a\x45\xdf\xa3"):
        return "webm"
    if head.startswith(b"ID3") or (len(head) > 1 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0):
        return "mp3"
    if head.startswith(b"OggS"):
        return "ogg"
    return None


def user_dir(settings: Settings, user_id: str) -> Path:
    base = Path(settings.upload_dir).resolve()
    d = (base / re.sub(r"[^0-9a-f-]", "", user_id.lower())).resolve()
    if not d.is_relative_to(base) or d == base:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad user id.")
    return d


def used_bytes(d: Path) -> int:
    return sum(p.stat().st_size for p in d.iterdir() if p.is_file()) if d.is_dir() else 0


def check_image(data: bytes, max_px: int | None) -> None:
    try:
        with Image.open(io.BytesIO(data)) as im:
            im.verify()
        with Image.open(io.BytesIO(data)) as im:
            w, h = im.size
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="That image can't be read.") from None
    if w * h > 40_000_000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="That image is too large (max 40 megapixels).")
    if max_px and (w > max_px or h > max_px):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cursors are {max_px}×{max_px} pixels at most.")


async def user_plan_rank(user_id: str) -> int:
    try:
        ent = await admin_db.user_plan(user_id)
    except (RuntimeError, OSError):
        return 0
    return plan_rank(ent["plan"]) if ent else 0


@router.post("", status_code=201)
async def upload(
    settings: SettingsDep,
    user: Annotated[User, Depends(require_user)],
    file: UploadFile = File(...),
    kind: str = Form(...),
) -> dict[str, Any]:
    spec = KINDS.get(kind)
    if spec is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown upload kind.")
    await rate_limit(f"rl:upload:{user.id}", 60, 3600)
    rank = await user_plan_rank(user.id)
    if rank < spec["plan"]:
        need = "Supporter" if spec["plan"] >= 2 else "Lifetime"
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"{kind.capitalize()} uploads come with {need} — a link works on every plan.")
    data = await file.read(spec["max"] + 1)
    if len(data) > spec["max"]:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"That file is over the {spec['max'] // MB or 1} MB limit for {kind} files.")
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file.")
    typ = sniff(data[:64])
    ext = spec["types"].get(typ or "")
    if not ext:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"That isn't a {'/'.join(spec['types'].values())} file.")
    if typ in ("png", "jpeg", "webp", "gif"):
        await run_in_threadpool(check_image, data, spec.get("max_px"))
    d = user_dir(settings, user.id)
    d.mkdir(parents=True, exist_ok=True)
    if used_bytes(d) + len(data) > QUOTA_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"You've used your {QUOTA_BYTES // MB} MB of hosting — delete something first.")
    name = f"{kind}-{hashlib.sha256(data).hexdigest()[:16]}.{ext}"
    (d / name).write_bytes(data)
    return {"url": f"/u/{d.name}/{name}", "kind": kind, "bytes": len(data), "used": used_bytes(d), "quota": QUOTA_BYTES}


@router.get("")
async def list_uploads(settings: SettingsDep, user: Annotated[User, Depends(require_user)]) -> dict[str, Any]:
    d = user_dir(settings, user.id)
    files = sorted(d.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True) if d.is_dir() else []
    return {"files": [{"name": p.name, "url": f"/u/{d.name}/{p.name}", "bytes": p.stat().st_size, "kind": p.name.split("-", 1)[0]} for p in files if p.is_file()],
            "used": used_bytes(d), "quota": QUOTA_BYTES}


@router.delete("/{name}")
async def delete_upload(name: str, settings: SettingsDep, user: Annotated[User, Depends(require_user)]) -> dict[str, Any]:
    if not NAME_RE.match(name):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such file.")
    d = user_dir(settings, user.id)
    p = d / name
    if not p.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such file.")
    p.unlink()
    return {"deleted": name, "used": used_bytes(d), "quota": QUOTA_BYTES}
