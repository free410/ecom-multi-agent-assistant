from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database: dict
    redis: dict


class APIMessage(BaseModel):
    message: str

