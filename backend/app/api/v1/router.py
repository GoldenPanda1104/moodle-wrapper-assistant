from fastapi import APIRouter

from app.api.v1.endpoints import events, moodle, tasks

api_router = APIRouter()
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(moodle.router, prefix="/moodle", tags=["moodle"])
