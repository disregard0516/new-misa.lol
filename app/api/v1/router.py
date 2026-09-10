import socket
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.profile import router as profile_router
from app.api.v1.admin import router as admin_router
from app.api.v1.uploads import router as uploads_router
from app.api.v1.reports import router as reports_router
from app.api.v1.explore import router as explore_router
from app.api.v1.guestbook import router as guestbook_router
from app.api.v1.presence import router as presence_router
from app.api.v1.nowplaying import router as nowplaying_router
from app.api.v1.doodles import router as doodles_router
from app.api.v1.weather import router as weather_router
from app.api.v1.linkcheck import router as linkcheck_router
from app.api.v1.replay import router as replay_router
from app.api.v1.asks import router as asks_router
from app.api.v1.vigil import router as vigil_router
from app.api.v1.tally import router as tally_router
from app.api.v1.neighbours import router as neighbours_router
from app.core.config import Settings, get_settings

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(profile_router)
api_router.include_router(admin_router)
api_router.include_router(uploads_router)
api_router.include_router(reports_router)
api_router.include_router(explore_router)
api_router.include_router(guestbook_router)
api_router.include_router(presence_router)
api_router.include_router(nowplaying_router)
api_router.include_router(doodles_router)
api_router.include_router(weather_router)
api_router.include_router(linkcheck_router)
api_router.include_router(replay_router)
api_router.include_router(asks_router)
api_router.include_router(vigil_router)
api_router.include_router(tally_router)
api_router.include_router(neighbours_router)


class RootResponse(BaseModel):
    service: str
    version: str


class InfoResponse(BaseModel):
    app: str
    instance: str
    hostname: str
    environment: str
    version: str
    time: datetime


@api_router.get("/", response_model=RootResponse, tags=["info"])
async def root(settings: Settings = Depends(get_settings)) -> RootResponse:
    return RootResponse(
        service=settings.app_name,
        version=settings.app_version,
    )


@api_router.get("/info", response_model=InfoResponse, tags=["info"])
async def info(settings: Settings = Depends(get_settings)) -> InfoResponse:
    return InfoResponse(
        app=settings.app_name,
        instance=settings.instance_name,
        hostname=socket.gethostname(),
        environment=settings.environment,
        version=settings.app_version,
        time=datetime.now(timezone.utc),
    )
