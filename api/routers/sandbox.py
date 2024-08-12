from fastapi import APIRouter, Depends, Request
from sqlalchemy.sql import text
from api.dependencies import get_session
from sqlmodel import Session
import logging


router = APIRouter(prefix="/sandbox", tags=["Sandbox"])


logger = logging.getLogger("expenses-tracker")


@router.post("/sql-sandbox")
async def sql_sandbox(
    request: Request, session: Session = Depends(get_session)
):
    body = await request.json()
    return {"message": "Query executed successfully"}
