"""Actualiza el documento de 'metrics' de la hora correspondiente cada vez que llega un sismo nuevo."""
from src.config.constants import COLLECTION_METRICS
from src.config.logging import get_logger
from src.database.mongodb import get_db
from src.metadata.validators import get_magnitude_range
from src.models.earthquake import EarthquakeEvent
from src.utils.time_windows import get_hour_window

logger = get_logger("services.metrics")


def update_metrics_for_event(event: EarthquakeEvent) -> None:
    db = get_db()
    window = get_hour_window(event.event_time)
    range_name = get_magnitude_range(event.magnitude)

    # Incrementamos contadores y maximo en una sola operacion atomica.
    # upsert=True crea el documento la primera vez que llega un sismo en esa hora.
    db[COLLECTION_METRICS].update_one(
        {"window": window},
        {
            "$inc": {
                "earthquake_count": 1,
                "sum_magnitude": event.magnitude,
                f"magnitude_distribution.{range_name}": 1,
            },
            "$max": {"max_magnitude": event.magnitude},
            "$setOnInsert": {"window": window},
        },
        upsert=True,
    )

    # El promedio no se puede calcular con un simple $inc, asi que lo
    # recalculamos leyendo el documento ya actualizado.
    metric_doc = db[COLLECTION_METRICS].find_one({"window": window})
    if metric_doc and metric_doc["earthquake_count"] > 0:
        avg_magnitude = metric_doc["sum_magnitude"] / metric_doc["earthquake_count"]
        db[COLLECTION_METRICS].update_one(
            {"window": window}, {"$set": {"avg_magnitude": round(avg_magnitude, 3)}}
        )

    logger.info(f"Metricas actualizadas para la ventana {window}")
