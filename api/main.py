from fastapi import FastAPI
from contextlib import asynccontextmanager
from logging.config import dictConfig
from api.routers import (
    users, recurrent_expenses, recurrent_savings, recurrent_incomes,
    categories, recurrent_budgets, expenses
)
from api.database import create_db_and_tables
from api.log_config import LogConfig
import uvicorn
import logging


dictConfig(LogConfig().model_dump())
logger = logging.getLogger("expenses-tracker")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Loading tables...')
    create_db_and_tables()
    yield
    logger.info('Shuting down...')


app = FastAPI(lifespan=lifespan)
app.include_router(users.router)
app.include_router(recurrent_expenses.router)
app.include_router(recurrent_savings.router)
app.include_router(recurrent_incomes.router)
app.include_router(recurrent_budgets.router)
app.include_router(categories.router)
app.include_router(expenses.router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
