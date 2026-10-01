"""Modelo interno de un sismo (lo que guardamos en Mongo)."""
from datetime import datetime

from pydantic import BaseModel


class EarthquakeEvent(BaseModel):
    """Un sismo ya transformado desde el formato de USGS a nuestro formato interno."""

    event_id: str
    magnitude: float
    location: str
    latitude: float
    longitude: float
    depth: float
    event_time: datetime

    def to_mongo_dict(self) -> dict:
        """Convierte el modelo a un diccionario listo para insertar en Mongo."""
        return self.model_dump()
