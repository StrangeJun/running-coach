import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel

from app.activities import NormalizedActivity
from app.activity_store import store_activity
from app.database import connect_database, initialize_database
from app.integrations.garmin import (
    DEFAULT_TOKEN_DIRECTORY, GarminAccessError, GarminClient, GarminDataError,
)

DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[2] / "data" / "running_coach.sqlite3"


class HealthResponse(BaseModel):
    status: str
    database: str


class ImportLatestResponse(BaseModel):
    status: Literal["imported", "already_exists"]
    activity: NormalizedActivity


def get_garmin_client() -> GarminClient:
    token_directory = Path(os.environ.get("RUNNING_COACH_GARMIN_TOKEN_DIR", str(DEFAULT_TOKEN_DIRECTORY)))
    # API requests use saved tokens only; first login/MFA belongs in the local CLI.
    return GarminClient(token_directory)


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

    @application.post(
        "/api/garmin/import-latest",
        response_model=ImportLatestResponse,
        responses={201: {"model": ImportLatestResponse, "description": "New activity imported"}},
    )
    def import_latest(
        response: Response,
        garmin: Annotated[GarminClient, Depends(get_garmin_client)],
    ) -> ImportLatestResponse:
        try:
            activity = garmin.latest_run()
        except GarminAccessError:
            raise HTTPException(
                status_code=503,
                detail="Garmin access unavailable; check the saved session with the local Garmin CLI",
            ) from None
        except GarminDataError:
            raise HTTPException(status_code=502, detail="Garmin returned invalid activity data") from None
        if activity is None:
            raise HTTPException(status_code=404, detail="No recent running activity found")
        try:
            stored, imported = store_activity(path, activity)
        except sqlite3.Error:
            raise HTTPException(status_code=503, detail="Activity storage unavailable") from None
        response.status_code = 201 if imported else 200
        return ImportLatestResponse(status="imported" if imported else "already_exists", activity=stored)

    return application


app = create_app()
