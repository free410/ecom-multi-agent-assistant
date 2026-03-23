from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database: dict[str, Any]
    redis: dict[str, Any]
    providers: dict[str, dict[str, Any]]


class APIMessage(BaseModel):
    message: str
