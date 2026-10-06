import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.database import connect_database, initialize_database

DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[2] / "data" / "running_coach.sqlite3"


class HealthResponse(BaseModel):
    status: str
    database: str


def create_app(database_path: Path | None = None) -> FastAPI:
    path = database_path if database_path is not None else Path(
        os.environ.get("RUNNING_COACH_DB_PATH", str(DEFAULT_DATABASE_PATH))
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        initialize_database(path)
        yield

    application = FastAPI(title="Running Coach API", lifespan=lifespan)

    @application.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        try:
            with connect_database(path) as connection:
                connection.execute("SELECT 1").fetchone()
        except sqlite3.Error:
            raise HTTPException(status_code=503, detail="Database unavailable") from None
        return HealthResponse(status="ok", database="ok")

    return application


app = create_app()
