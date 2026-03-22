from fastapi import APIRouter

from app.core.database import get_database_status
from app.core.redis_client import redis_store
from app.schemas.common import HealthResponse


router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    db_status = get_database_status()
    redis_status = redis_store.status()
    status = "ok" if db_status["available"] or redis_status["available"] else "degraded"
    return HealthResponse(status=status, database=db_status, redis=redis_status)

