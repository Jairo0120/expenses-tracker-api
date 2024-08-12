from fastapi import FastAPI
from contextlib import asynccontextmanager
from logging.config import dictConfig
from api.routers import (
    users,
    recurrent_expenses,
    recurrent_savings,
    recurrent_incomes,
    categories,
    recurrent_budgets,
    expenses,
    budgets,
    sandbox
)
from api.database import create_db_and_tables
from api.log_config import LogConfig
from mangum import Mangum
import uvicorn
import logging
import os


dictConfig(LogConfig().model_dump())
logger = logging.getLogger("expenses-tracker")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading tables...")
    create_db_and_tables()
    yield
    logger.info("Shuting down...")


# ENV environment variable only used in AWS Lambda. It is used to set the
# root path of the API Gateway and avoid the error showing the documentation.
# More info:
# https://fastapi.tiangolo.com/advanced/behind-a-proxy/#behind-a-proxy
env = os.getenv("ENV")
app = FastAPI(lifespan=lifespan, root_path=f"/{env}" if env else "")
app.include_router(users.router)
app.include_router(recurrent_expenses.router)
app.include_router(recurrent_savings.router)
app.include_router(recurrent_incomes.router)
app.include_router(recurrent_budgets.router)
app.include_router(categories.router)
app.include_router(expenses.router)
app.include_router(budgets.router)
app.include_router(sandbox.router)

handler = Mangum(app, lifespan="on")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
