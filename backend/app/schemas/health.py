"""Health-check payload."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Liveness payload. The disclaimer is included so API clients cannot drop it."""

    status: str = Field(examples=["ok"])
    service: str = "preventvital"
    database: str
    disclaimer: str
