"""
Servicio de procesamiento (el "consumidor" de RabbitMQ).

Responsabilidad unica: recibir un sismo desde la cola, guardarlo en
MongoDB y actualizar las metricas de esa hora. Si el sismo ya existia
(porque por ejemplo la ingesta se reinicio y perdio su cache), Mongo
rechaza el insert gracias al indice unico en 'event_id' y simplemente
lo ignoramos.
"""
from prometheus_client import Counter
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError

from src.config.constants import COLLECTION_EARTHQUAKES
from src.config.logging import get_logger
from src.database.mongodb import get_db
from src.models.earthquake import EarthquakeEvent
from src.services.metrics_service import update_metrics_for_event

logger = get_logger("services.processing")

EVENTS_SAVED = Counter("processing_events_saved_total", "Sismos guardados en MongoDB")
EVENTS_REJECTED = Counter("processing_events_rejected_total", "Mensajes invalidos o duplicados")


def process_earthquake_message(event_dict: dict) -> None:
    try:
        event = EarthquakeEvent(**event_dict)
    except ValidationError as error:
        logger.error(f"Mensaje invalido recibido de RabbitMQ: {error}")
        EVENTS_REJECTED.inc()
        return

    db = get_db()

    try:
        db[COLLECTION_EARTHQUAKES].insert_one(event.to_mongo_dict())
    except DuplicateKeyError:
        logger.info(f"Sismo {event.event_id} ya existia, se ignora")
        EVENTS_REJECTED.inc()
        return

    update_metrics_for_event(event)
    EVENTS_SAVED.inc()
    logger.info(f"Sismo {event.event_id} guardado correctamente")
