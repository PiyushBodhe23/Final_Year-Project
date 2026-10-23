"""PreventVital HTTP entry. Feature endpoints are added in later phases."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from backend.app.core.config import DISCLAIMER, database_url
from backend.app.core.db import Base, engine
from backend.app.models import tables as _tables  # noqa: F401
from backend.app.api.patients import router as patients_router
from backend.app.schemas.health import HealthResponse


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Create any missing tables so the SQLite demo runs without a manual migrate."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="PreventVital",
    description=DISCLAIMER,
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(patients_router)

cors_origins_env = os.environ.get("CORS_ORIGINS", "")
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
if cors_origins_env:
    allowed_origins.extend([o.strip() for o in cors_origins_env.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.environ.get("ALLOW_ALL_CORS") == "1" else allowed_origins,
    allow_origin_regex=r"^https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Report process and database liveness. This is not a clinical status."""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    backend = "sqlite" if database_url().startswith("sqlite") else "external"
    return HealthResponse(status="ok", database=backend, disclaimer=DISCLAIMER)
