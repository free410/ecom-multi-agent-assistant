import json
import logging
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.core.database as database
from app.core.config import get_settings
from app.models.product import Product


logger = logging.getLogger(__name__)

GENERIC_CATEGORY_ALIASES: dict[str, list[str]] = {
    "手机": ["手机", "智能手机", "旗舰手机", "拍照手机", "游戏手机"],
    "咖啡杯": ["咖啡杯", "保温杯", "水杯", "随行杯"],
    "榨汁杯": ["榨汁杯", "便携榨汁机", "果汁杯"],
    "香薰机": ["香薰机", "香氛机", "扩香机"],
    "风扇": ["风扇", "桌面风扇", "小风扇", "随身风扇"],
    "耳机": ["耳机", "蓝牙耳机", "降噪耳机"],
    "音箱": ["音箱", "蓝牙音箱", "便携音箱"],
    "充电宝": ["充电宝", "移动电源"],
    "台灯": ["台灯", "护眼灯", "阅读灯"],
    "电动牙刷": ["电动牙刷", "牙刷"],
}

GENERIC_SUBJECT_STOPWORDS = {
    "一个",
    "一款",
    "一部",
    "一台",
    "一种",
    "这款",
    "这个",
    "那个",
    "产品",
    "商品",
    "文案",
    "活动",
    "促销",
    "618",
    "双11",
    "卖点",
    "客服",
    "回复",
    "评论",
    "差评",
    "竞品",
    "日报",
    "分析",
    "总结",
    "问题",
    "任务",
    "内容",
    "运营",
}


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
        if not product_name.strip():
            return None

        normalized_query = self._normalize_text(product_name)
        best_product = None
        best_score = 0.0

        for product in self.get_products(db=db):
            score = self._product_match_score(normalized_query, product["name"])
            if score > best_score:
                best_score = score
                best_product = product

        return best_product if best_score >= 0.45 else None

    def get_reviews(self, product_id: int | None = None) -> list[dict[str, Any]]:
        if product_id is None:
            return list(self._memory_reviews)
        return [item for item in self._memory_reviews if item["product_id"] == product_id]

    def get_competitors(self, product_name: str | None = None) -> list[dict[str, Any]]:
        if not product_name:
            return list(self._memory_competitors)

        matched_product = self.find_product(product_name)
        canonical_name = matched_product["name"] if matched_product else product_name
        normalized = self._normalize_text(canonical_name)
        return [
            item
            for item in self._memory_competitors
            if self._normalize_text(item["product_name"]) == normalized
            or normalized in self._normalize_text(item["product_name"])
        ]

    def detect_product_name(self, message: str, db: Session | None = None) -> str | None:
        normalized_message = self._normalize_text(message)
        best_name = None
        best_score = 0.0

        for product in self.get_products(db=db):
            score = self._message_product_score(normalized_message, product["name"])
            if score > best_score:
                best_score = score
                best_name = product["name"]

        return best_name if best_score >= 0.5 else None

    def detect_subject(self, message: str, db: Session | None = None) -> dict[str, str | None]:
        product_name = self.detect_product_name(message, db=db)
        if product_name:
            return {
                "product_name": product_name,
                "subject_name": product_name,
                "subject_type": "seed_product",
            }

        category_name = self._detect_category_name(message)
        if category_name:
            return {
                "product_name": None,
                "subject_name": category_name,
                "subject_type": "category",
            }

        freeform_subject = self._extract_freeform_subject(message)
        if freeform_subject:
            return {
                "product_name": None,
                "subject_name": freeform_subject,
                "subject_type": "freeform",
            }

        return {
            "product_name": None,
            "subject_name": None,
            "subject_type": None,
        }

    def build_generic_product_profile(self, subject_name: str) -> dict[str, Any]:
        normalized = self._normalize_text(subject_name)
        category_name = self._detect_category_name(subject_name) or subject_name

        profile_templates: dict[str, dict[str, Any]] = {
            "手机": {
                "selling_points": ["高颜值外观", "流畅性能", "拍照体验强", "续航稳定"],
                "target_users": ["学生", "上班族", "数码爱好者"],
                "faq": [
                    {"question": "适合什么人群？", "answer": "适合重视颜值、性能和日常体验的用户。"},
                    {"question": "主打卖点是什么？", "answer": "主打流畅体验、影像能力和续航表现。"},
                ],
                "after_sale_policy": "支持 7 天无理由退货与 1 年基础保修。",
            },
            "耳机": {
                "selling_points": ["佩戴舒适", "音质均衡", "连接稳定", "通勤便携"],
                "target_users": ["通勤人群", "学生", "运动爱好者"],
                "faq": [
                    {"question": "适合哪些场景？", "answer": "适合通勤、学习、会议和轻运动场景。"},
                    {"question": "购买时关注什么？", "answer": "可以重点关注佩戴、续航和降噪表现。"},
                ],
                "after_sale_policy": "支持 7 天无理由退货和基础售后质保。",
            },
        }

        template = profile_templates.get(category_name, None)
        if template is None:
            template = {
                "selling_points": ["高颜值设计", "核心功能清晰", "适合电商转化表达", "可突出品质与性价比"],
                "target_users": ["目标消费人群", "注重体验的用户"],
                "faq": [
                    {"question": "适合哪些人群？", "answer": f"适合对 {category_name} 有明确购买需求的用户。"},
                    {"question": "推荐卖点怎么写？", "answer": "可以从场景、体验、品质和售后四个维度展开。"},
                ],
                "after_sale_policy": "支持常规售后服务，可根据店铺规则补充细节。",
            }

        return {
            "id": 0,
            "name": subject_name,
            "category": category_name,
            "selling_points": template["selling_points"],
            "price": 0,
            "target_users": template["target_users"],
            "faq": template["faq"],
            "after_sale_policy": template["after_sale_policy"],
            "source": "generic",
            "normalized": normalized,
        }

    @staticmethod
    def _normalize_text(value: str) -> str:
        return re.sub(r"[^0-9a-zA-Z\u4e00-\u9fa5]", "", value).lower()

    def _product_match_score(self, normalized_query: str, product_name: str) -> float:
        normalized_name = self._normalize_text(product_name)
        if not normalized_query or not normalized_name:
            return 0.0
        if normalized_query == normalized_name:
            return 1.0
        if normalized_query in normalized_name or normalized_name in normalized_query:
            return 0.92
        return SequenceMatcher(None, normalized_query, normalized_name).ratio()

    def _message_product_score(self, normalized_message: str, product_name: str) -> float:
        normalized_name = self._normalize_text(product_name)
        if not normalized_message or not normalized_name:
            return 0.0
        if normalized_name in normalized_message:
            return 1.0

        aliases = {normalized_name}
        for suffix_len in range(3, min(7, len(normalized_name) + 1)):
            aliases.add(normalized_name[-suffix_len:])

        best_score = 0.0
        for alias in aliases:
            if alias and alias in normalized_message:
                best_score = max(best_score, 0.72 if alias != normalized_name else 1.0)

        if best_score > 0:
            return best_score

        return SequenceMatcher(None, normalized_message, normalized_name).ratio()

    def _detect_category_name(self, message: str) -> str | None:
        normalized_message = self._normalize_text(message)
        for category, aliases in GENERIC_CATEGORY_ALIASES.items():
            for alias in aliases:
                if self._normalize_text(alias) in normalized_message:
                    return category
        return None

    def _extract_freeform_subject(self, message: str) -> str | None:
        patterns = [
            r"(?:写|做|生成|给我写|帮我写|帮我做|想要|需要)(?:一个|一条|一版|一份|一款|一部|一台)?(?P<subject>[\u4e00-\u9fa5A-Za-z0-9]{2,18})(?:的)?(?:文案|卖点|回复|分析|介绍|问答)",
            r"(?P<subject>[\u4e00-\u9fa5A-Za-z0-9]{2,18})(?:的)?(?:文案|卖点|回复|分析|介绍|问答)",
            r"(?:我说的是|就是|要的是)(?P<subject>[\u4e00-\u9fa5A-Za-z0-9]{2,18})",
        ]
        for pattern in patterns:
            match = re.search(pattern, message)
            if not match:
                continue
            subject = self._clean_subject_candidate(match.group("subject").strip())
            if self._is_valid_freeform_subject(subject):
                return subject

        normalized_message = self._normalize_text(message)
        cleaned_message = self._clean_subject_candidate(message.strip())
        if 2 <= len(normalized_message) <= 12 and self._is_valid_freeform_subject(cleaned_message):
            return cleaned_message
        return None

    def _is_valid_freeform_subject(self, value: str) -> bool:
        normalized = self._normalize_text(value)
        if not normalized or normalized in {self._normalize_text(item) for item in GENERIC_SUBJECT_STOPWORDS}:
            return False
        if normalized.isdigit():
            return False
        if any(token in normalized for token in ["给我", "帮我", "生成", "写", "做", "需要", "想要"]):
            return False
        if any(token in normalized for token in ["促销", "活动", "文案", "卖点", "客服", "竞品", "评论", "日报"]):
            return False
        return len(normalized) >= 2

    @staticmethod
    def _clean_subject_candidate(value: str) -> str:
        cleaned = value.strip()
        patterns = [
            r"^(给我|帮我|请|想要|需要|来个|做个)",
            r"^(生成|写|做)",
            r"^(一个|一条|一段|一版|一份|一款|一部|一台|这种|这款|这个|那个)",
        ]
        changed = True
        while changed and cleaned:
            previous = cleaned
            for pattern in patterns:
                cleaned = re.sub(pattern, "", cleaned)
            cleaned = cleaned.strip()
            changed = cleaned != previous
        cleaned = re.sub(r"(促销|活动|文案|卖点|客服|回复|评论|竞品|日报)$", "", cleaned)
        return cleaned.strip()

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
