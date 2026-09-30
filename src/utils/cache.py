"""
Cache muy simple en memoria, con expiracion (TTL = "time to live").

La usamos en la API para no golpear MongoDB con consultas de agregacion
(metricas y reportes) en cada request, si varios clientes piden lo
mismo en un periodo corto de tiempo.

No es apta para correr con varias replicas de la API (cada una tendria
su propia cache), pero para el alcance de esta prueba tecnica es
suficiente y muy facil de entender.
"""
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
            # Expiro, la borramos y decimos que no habia nada.
            del self._store[key]
            return None

        return value

    def set(self, key: str, value) -> None:
        self._store[key] = (time.time(), value)
