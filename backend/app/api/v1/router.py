from fastapi import APIRouter

from app.api.v1.endpoints import events, moodle, tasks, auth, vault, notifications

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(moodle.router, prefix="/moodle", tags=["moodle"])
api_router.include_router(vault.router, prefix="/vault", tags=["vault"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
