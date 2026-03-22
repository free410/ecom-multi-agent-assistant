import json
import logging
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.core.database as database
from app.core.config import get_settings
from app.models.product import Product


logger = logging.getLogger(__name__)


class SeedService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._memory_products: list[dict[str, Any]] = []
        self._memory_reviews: list[dict[str, Any]] = []
        self._memory_competitors: list[dict[str, Any]] = []
        self._load_seed_files()

    def _read_json(self, file_path: Path) -> list[dict[str, Any]]:
        with file_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _load_seed_files(self) -> None:
        seed_dir = self.settings.seed_dir
        self._memory_products = self._read_json(seed_dir / "products.json")
        self._memory_reviews = self._read_json(seed_dir / "reviews.json")
        self._memory_competitors = self._read_json(seed_dir / "competitors.json")

    def bootstrap(self, db: Session | None = None) -> None:
        if not database.db_available or db is None:
            logger.info("Seed data loaded into memory mode.")
            return

        existing = db.scalar(select(Product.id).limit(1))
        if existing:
            return

        for product in self._memory_products:
            db.add(Product(**product))
        db.commit()
        logger.info("Seed products inserted into database.")

    def initialize_data(self, db: Session | None = None) -> dict[str, Any]:
        self._load_seed_files()
        if database.db_available and db is not None:
            db.query(Product).delete()
            for product in self._memory_products:
                db.add(Product(**product))
            db.commit()
            mode = "mysql"
        else:
            mode = "memory"

        return {
            "message": "Mock seed data initialized successfully.",
            "product_count": len(self._memory_products),
            "review_count": len(self._memory_reviews),
            "competitor_count": len(self._memory_competitors),
            "database_mode": mode,
        }

    def get_products(self, db: Session | None = None) -> list[dict[str, Any]]:
        if database.db_available and db is not None:
            products = db.scalars(select(Product).order_by(Product.id)).all()
            if products:
                return [self._product_to_dict(item) for item in products]
        return list(self._memory_products)

    def find_product(self, product_name: str, db: Session | None = None) -> dict[str, Any] | None:
        normalized = product_name.strip().lower()
        for product in self.get_products(db=db):
            if normalized in product["name"].lower() or product["name"].lower() in normalized:
                return product
        return None

    def get_reviews(self, product_id: int | None = None) -> list[dict[str, Any]]:
        if product_id is None:
            return list(self._memory_reviews)
        return [item for item in self._memory_reviews if item["product_id"] == product_id]

    def get_competitors(self, product_name: str | None = None) -> list[dict[str, Any]]:
        if not product_name:
            return list(self._memory_competitors)
        normalized = product_name.strip().lower()
        return [
            item
            for item in self._memory_competitors
            if item["product_name"].lower() == normalized or normalized in item["product_name"].lower()
        ]

    def detect_product_name(self, message: str, db: Session | None = None) -> str | None:
        lowered = message.lower()
        for product in self.get_products(db=db):
            name = product["name"]
            if name.lower() in lowered:
                return name
        return None

    @staticmethod
    def _product_to_dict(product: Product) -> dict[str, Any]:
        return {
            "id": product.id,
            "name": product.name,
            "category": product.category,
            "selling_points": product.selling_points,
            "price": product.price,
            "target_users": product.target_users,
            "faq": product.faq,
            "after_sale_policy": product.after_sale_policy,
        }


seed_service = SeedService()
