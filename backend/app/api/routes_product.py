from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.product import ProductResponse, SeedInitResponse
from app.services.seed_service import seed_service


router = APIRouter(prefix="/api", tags=["products"])


@router.get("/products", response_model=list[ProductResponse])
def get_products(db: Session | None = Depends(get_db)) -> list[ProductResponse]:
    return [ProductResponse(**item) for item in seed_service.get_products(db=db)]


@router.post("/seed/init", response_model=SeedInitResponse)
def init_seed(db: Session | None = Depends(get_db)) -> SeedInitResponse:
    payload = seed_service.initialize_data(db=db)
    return SeedInitResponse(**payload)

