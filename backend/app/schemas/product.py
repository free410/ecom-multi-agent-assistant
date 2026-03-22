from pydantic import BaseModel


class ProductResponse(BaseModel):
    id: int
    name: str
    category: str
    selling_points: list[str]
    price: float
    target_users: list[str]
    faq: list[dict]
    after_sale_policy: str


class SeedInitResponse(BaseModel):
    message: str
    product_count: int
    review_count: int
    competitor_count: int
    database_mode: str

