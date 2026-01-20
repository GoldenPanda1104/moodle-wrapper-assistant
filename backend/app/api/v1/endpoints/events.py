from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.crud import event_log as crud_event_log
from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.schemas.event_log import EventLogCreate, EventLogRead
from app.services.event_service import log_event

router = APIRouter()


@router.get("/", response_model=list[EventLogRead])
def list_events(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    event_type: str | None = None,
    source: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return crud_event_log.list_event_logs(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        event_type=event_type,
        source=source,
    )


@router.post("/", response_model=EventLogRead, status_code=status.HTTP_201_CREATED)
def create_event(
    event_in: EventLogCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return log_event(
            db,
            event_type=event_in.event_type,
            source=event_in.source,
            payload=event_in.payload or {},
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
