"""
Creacion de indices de MongoDB.

Se ejecuta al arrancar el servicio de ingesta y la API (crear un indice
que ya existe no hace nada, asi que es seguro llamarlo varias veces).

Decisiones de diseno (explicadas tambien en el README):
- earthquakes.event_id es UNIQUE: es la forma mas simple y segura de
  evitar duplicados, dejamos que Mongo rechace el insert repetido en
  vez de nosotros tener que revisar "a mano" si el evento ya existe.
- earthquakes.event_time: casi todas las consultas (ultimos sismos,
  reportes por hora) filtran u ordenan por fecha.
- earthquakes.magnitude: se usa mucho para filtrar por rango de magnitud.
- metrics.window es UNIQUE: cada ventana de una hora tiene un solo
  documento que se va actualizando (upsert).
- hourly_reports.report_date es UNIQUE: si el DAG de Airflow se vuelve a
  ejecutar para la misma hora, actualiza el reporte en vez de duplicarlo.
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
