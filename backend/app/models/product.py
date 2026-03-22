from sqlalchemy import JSON, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    selling_points: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    target_users: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    faq: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    after_sale_policy: Mapped[str] = mapped_column(String(1000), nullable=False)
