"""Cache simple en memoria con expiracion (TTL), usada en la API para /metrics y /reports."""
import time


class SimpleCache:
    def __init__(self, ttl_seconds: int):
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[float, object]] = {}

    def get(self, key: str):
        entry = self._store.get(key)
        if entry is None:
            return None

        saved_at, value = entry
        if time.time() - saved_at > self.ttl_seconds:
            del self._store[key]
            return None

        return value

    def set(self, key: str, value) -> None:
        self._store[key] = (time.time(), value)
