from datetime import date
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel as Schema
from sqlmodel import Session
from api.dependencies import get_current_active_user, get_session
from api.models import User
from api import sync
import logging


logger = logging.getLogger("expenses-tracker")
router = APIRouter(prefix="/sync", tags=["Sync"])


class PullResponse(Schema):
    cursor: int
    has_more: bool
    # Entity name (e.g. "expenses") -> changed records, in dependency order.
    changes: dict[str, list[dict[str, Any]]]


class CycleRecordsResponse(Schema):
    # Entity name -> the cycle's live records (budgets, expenses, incomes).
    changes: dict[str, list[dict[str, Any]]]


class PushResponse(Schema):
    results: list[sync.PushResult]


@router.get("", response_model=PullResponse)
def pull_changes(
    since: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=2000),
    window_start: date | None = Query(
        None,
        description="Only budgets, expenses and incomes of cycles starting "
        "on or after this date",
    ),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    logger.info(f"Sync pull for user {current_user.id} since {since}")
    return sync.pull(
        session, current_user.id or 0, since, limit, window_start
    )


@router.get("/cycles/{cycle_uuid}", response_model=CycleRecordsResponse)
def cycle_records(
    cycle_uuid: str,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """For cycles older than a client's sync window."""
    records = sync.cycle_records(session, current_user.id or 0, cycle_uuid)
    if records is None:
        raise HTTPException(status_code=404, detail="Cycle not found")
    return records


@router.post("", response_model=PushResponse)
def push_changes(
    request: sync.PushRequest,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    logger.info(
        f"Sync push of {len(request.changes)} changes "
        f"for user {current_user.id}"
    )
    processor = sync.PushProcessor(session, current_user.id or 0)
    return {"results": processor.run(request.changes)}
