import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status
from app.api.v1.router import api_router
from app.core.config import settings
from app.services.scheduler import start_scheduler, stop_scheduler

app = FastAPI(title=settings.PROJECT_NAME)

# Rutas bajo /api/v1 (cuando el tráfico pasa por el frontend nginx o el proxy no modifica el path)
app.include_router(api_router, prefix="/api/v1")
# Rutas bajo /v1 por si Traefik u otro proxy enruta /api/* al backend quitando el prefijo /api
app.include_router(api_router, prefix="/v1")

@app.on_event("startup")
def on_startup() -> None:
    start_scheduler()


@app.on_event("shutdown")
def on_shutdown() -> None:
    stop_scheduler()

@app.get("/health")
def health_check():
    return {"status": "ok"}


def _error_payload(code: str, message: str, details: object | None = None) -> dict[str, object]:
    error: dict[str, object] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return {"error": error}


@app.exception_handler(HTTPException)
def handle_http_exception(request: Request, exc: HTTPException):
    logging.getLogger("api").warning("HTTP %s %s: %s", exc.status_code, request.url.path, exc.detail)
    payload = _error_payload("http_error", str(exc.detail))
    payload["detail"] = exc.detail
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(RequestValidationError)
def handle_validation_error(request: Request, exc: RequestValidationError):
    payload = _error_payload("validation_error", "Invalid request", exc.errors())
    payload["detail"] = exc.errors()
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload)


@app.exception_handler(Exception)
def handle_unexpected_error(request: Request, exc: Exception):
    logging.getLogger("api").exception("Unhandled error on %s", request.url.path)
    payload = _error_payload("server_error", "Internal server error")
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload)
