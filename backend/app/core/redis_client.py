import json
import logging
from typing import Any

from redis import Redis

from app.core.config import get_settings


logger = logging.getLogger(__name__)


class RedisStore:
    def __init__(self) -> None:
        self.client: Redis | None = None
        self.available = False
        self.error_message = ""
        self._memory_store: dict[str, str] = {}

    def init(self) -> None:
        settings = get_settings()
        if not settings.redis_url:
            self.available = False
            self.error_message = "REDIS_URL not configured. Using in-memory cache."
            logger.warning(self.error_message)
            return

        try:
            self.client = Redis.from_url(settings.redis_url, decode_responses=True)
            self.client.ping()
            self.available = True
            self.error_message = ""
            logger.info("Redis connected successfully.")
        except Exception as exc:
            self.available = False
            self.error_message = f"Redis unavailable: {exc}"
            self.client = None
            logger.warning(self.error_message)

    def get_json(self, key: str, default: Any = None) -> Any:
        payload = None
        if self.available and self.client is not None:
            payload = self.client.get(key)
        else:
            payload = self._memory_store.get(key)

        if payload is None:
            return default

        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return default

    def set_json(self, key: str, value: Any, expire_seconds: int | None = None) -> None:
        payload = json.dumps(value, ensure_ascii=False)
        if self.available and self.client is not None:
            self.client.set(key, payload, ex=expire_seconds)
            return
        self._memory_store[key] = payload

    def append_message(self, session_id: str, role: str, content: str) -> list[dict[str, str]]:
        key = f"session:{session_id}:history"
        history = self.get_json(key, default=[]) or []
        history.append({"role": role, "content": content})
        self.set_json(key, history, expire_seconds=60 * 60 * 24)
        return history

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        return self.get_json(f"session:{session_id}:history", default=[]) or []

    def set_last_result(self, session_id: str, result: dict[str, Any]) -> None:
        self.set_json(f"session:{session_id}:last_result", result, expire_seconds=60 * 60 * 24)

    def get_last_result(self, session_id: str) -> dict[str, Any] | None:
        return self.get_json(f"session:{session_id}:last_result", default=None)

    def status(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "message": "ok" if self.available else self.error_message,
        }


redis_store = RedisStore()

