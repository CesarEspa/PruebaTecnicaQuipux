"""
Servicio de ingesta: consulta la API de USGS, detecta sismos nuevos y
los publica en RabbitMQ. No escribe en Mongo directamente, eso lo hace
el servicio de procesamiento que escucha la cola.
"""
from prometheus_client import Counter

from src.clients.usgs_client import fetch_latest_earthquakes
from src.config.logging import get_logger
from src.messaging.broker import publish_earthquake_event
from src.metadata.validators import parse_usgs_feature
from src.utils.cache import SimpleCache

logger = get_logger("services.ingestion")

EVENTS_FETCHED = Counter("ingestion_events_fetched_total", "Sismos recibidos desde USGS")
EVENTS_PUBLISHED = Counter("ingestion_events_published_total", "Sismos nuevos publicados en RabbitMQ")
EVENTS_DUPLICATED = Counter("ingestion_events_duplicated_total", "Sismos ignorados por ser duplicados")

# La API trae siempre los sismos de la ultima hora, asi que el mismo sismo
# puede repetirse en varios ciclos seguidos. Esta cache evita republicarlo.
_seen_events_cache = SimpleCache(ttl_seconds=70 * 60)


def run_ingestion_cycle() -> None:
    """Corre un ciclo completo: trae datos de USGS y publica los sismos nuevos."""
    features = fetch_latest_earthquakes()
    EVENTS_FETCHED.inc(len(features))

    new_events = 0
    skipped_duplicates = 0
    invalid_features = 0

    for feature in features:
        event = parse_usgs_feature(feature)

        if event is None:
            invalid_features += 1
            continue

        if _seen_events_cache.get(event.event_id) is not None:
            skipped_duplicates += 1
            EVENTS_DUPLICATED.inc()
            continue

        _seen_events_cache.set(event.event_id, True)
        publish_earthquake_event(event.model_dump(mode="json"))
        EVENTS_PUBLISHED.inc()
        new_events += 1

    logger.info(
        "Ciclo de ingesta terminado: "
        f"recibidos={len(features)}, nuevos={new_events}, "
        f"duplicados={skipped_duplicates}, invalidos={invalid_features}"
    )
