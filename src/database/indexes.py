"""
Creacion de indices de Mongo. Se llama al arrancar la API y el consumer
(crear un indice que ya existe no hace nada, es seguro llamarlo varias veces).

event_id es unico para evitar duplicados sin tener que revisarlo a mano.
window y report_date tambien son unicos porque cada hora tiene un solo
documento que se actualiza (upsert) en vez de crear uno nuevo cada vez.
"""
from src.config.constants import (
    COLLECTION_EARTHQUAKES,
    COLLECTION_HOURLY_REPORTS,
    COLLECTION_METRICS,
)
from src.config.logging import get_logger
from src.database.mongodb import get_db

logger = get_logger("database.indexes")


def create_indexes() -> None:
    db = get_db()

    db[COLLECTION_EARTHQUAKES].create_index("event_id", unique=True)
    db[COLLECTION_EARTHQUAKES].create_index("event_time")
    db[COLLECTION_EARTHQUAKES].create_index("magnitude")

    db[COLLECTION_METRICS].create_index("window", unique=True)

    db[COLLECTION_HOURLY_REPORTS].create_index("report_date", unique=True)

    logger.info("Indices de MongoDB verificados/creados correctamente")
