"""Transforma los datos crudos de USGS a nuestro modelo interno."""
from datetime import datetime, timezone

from src.config.constants import MAGNITUDE_RANGES
from src.models.earthquake import EarthquakeEvent


def parse_usgs_feature(feature: dict) -> EarthquakeEvent | None:
    """Convierte un feature del GeoJSON de USGS en un EarthquakeEvent, o None si viene incompleto."""
    try:
        properties = feature["properties"]
        coordinates = feature["geometry"]["coordinates"]
        longitude, latitude, depth = coordinates[0], coordinates[1], coordinates[2]

        magnitude = properties.get("mag")
        event_time_ms = properties.get("time")

        if magnitude is None or event_time_ms is None:
            return None

        event_time = datetime.fromtimestamp(event_time_ms / 1000, tz=timezone.utc)

        return EarthquakeEvent(
            event_id=feature["id"],
            magnitude=magnitude,
            location=properties.get("place") or "Unknown location",
            latitude=latitude,
            longitude=longitude,
            depth=depth,
            event_time=event_time,
        )
    except (KeyError, IndexError, TypeError):
        return None


def get_magnitude_range(magnitude: float) -> str:
    """Devuelve el nombre del rango de magnitud al que pertenece un sismo."""
    for range_name, min_value, max_value in MAGNITUDE_RANGES:
        if min_value <= magnitude < max_value:
            return range_name
    return MAGNITUDE_RANGES[-1][0]
