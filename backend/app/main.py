import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_chat import router as chat_router
from app.api.routes_health import router as health_router
from app.api.routes_product import router as product_router
from app.api.routes_session import router as session_router
from app.core.config import get_settings
import app.core.database as database
from app.core.redis_client import redis_store
from app.services.seed_service import seed_service


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.init_database()
    redis_store.init()

    if database.SessionLocal is not None:
        with database.SessionLocal() as db:
            seed_service.bootstrap(db=db)
    else:
        seed_service.bootstrap(db=None)
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(product_router)
app.include_router(session_router)
