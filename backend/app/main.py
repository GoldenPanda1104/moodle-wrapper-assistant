from fastapi import FastAPI
from app.api.v1.router import api_router
from app.core.config import settings
from app.services.scheduler import start_scheduler, stop_scheduler

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
def on_startup() -> None:
    start_scheduler()


@app.on_event("shutdown")
def on_shutdown() -> None:
    stop_scheduler()

@app.get("/health")
def health_check():
    return {"status": "ok"}
